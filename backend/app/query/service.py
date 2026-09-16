"""Answering questions, and the conversation history that makes follow-ups work."""
from __future__ import annotations

import json
import time
import uuid
from datetime import UTC, datetime

import logfire
from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool
from fastapi.encoders import jsonable_encoder
from langchain_core.messages import AIMessage, HumanMessage
from redis.asyncio import Redis

from app.connections import service as connections_service
from app.core.config import settings
from app.query.agent.errors import classify as classify_model_failure
from app.query.agent.loop import run_agent

# Imported as a module: this package also defines a create_connection.
from app.query.databases import connections as target_db
from app.session import store
from app.session.store import SessionData

from .schemas import (
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationSummary,
    MessageResponse,
    NaturalLanguageQueryRequest,
    NaturalLanguageQueryResponse,
)

# Turns replayed to the agent. Each turn is a question plus the SQL answering it,
# so this bounds how much of a long conversation reaches the prompt.
MAX_HISTORY_MESSAGES = settings.MAX_HISTORY_MESSAGES


def _now() -> str:
    return datetime.now(UTC).isoformat()


async def _load_conversation(
    session: SessionData, connection_id: str, conversation_id: str, redis: Redis
) -> dict:
    """Fetch a conversation, scoped to this session and connection."""
    raw = await redis.hget(store.conversations_key(session.sid), conversation_id)
    record = json.loads(raw) if raw else None
    if record is None or record["connection_id"] != connection_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Conversation not found"},
        )
    return record


async def _load_messages(
    session: SessionData, conversation_id: str, redis: Redis, limit: int | None = None
) -> list[dict]:
    """Messages oldest first; `limit` takes the most recent N."""
    key = store.messages_key(session.sid, conversation_id)
    start = -limit if limit else 0
    return [json.loads(m) for m in await redis.lrange(key, start, -1)]


def _to_agent_history(messages: list[dict]) -> list:
    """Convert stored messages into the message objects the agent expects.

    An assistant turn's SQL is replayed alongside its prose: the query is the
    substantive artifact a follow-up builds on ("now filter that by 2024"),
    which plain answer text alone would not carry.
    """
    out = []
    for m in messages:
        if m["role"] == "user":
            out.append(HumanMessage(content=m["content"]))
            continue
        sql = m.get("sql_query")
        parts = [p for p in (m["content"], f"SQL: {sql}" if sql else "") if p]
        out.append(AIMessage(content="\n".join(parts)))
    return out


def _engine_for(record: dict):
    """An engine for a stored connection, decrypting its password on the way."""
    password = connections_service.record_password(record)
    return target_db.create_connection(
        record["db_type"],
        record["host"],
        record["port"],
        record["username"],
        password,
        record["database_name"],
    )


async def ask(
    session: SessionData,
    connection_id: str,
    body: NaturalLanguageQueryRequest,
    redis: Redis,
) -> NaturalLanguageQueryResponse:
    """Answer a natural language question with the SQL agent, in conversation context."""
    logfire.info(
        "Question in session {session_id} against connection {connection_id}",
        session_id=session.sid,
        connection_id=connection_id,
    )

    record = await connections_service.get_record(session, connection_id, redis)
    engine = _engine_for(record)

    conversation_id = body.conversation_id
    conversation = None
    history = []
    if conversation_id:
        conversation = await _load_conversation(session, connection_id, conversation_id, redis)
        history = _to_agent_history(
            await _load_messages(session, conversation_id, redis, MAX_HISTORY_MESSAGES)
        )
        logfire.info(
            "Continuing conversation {conversation_id} with {history_messages} prior message(s)",
            conversation_id=conversation_id,
            history_messages=len(history),
        )

    # Measured around the agent alone -- not the Redis reads above or the
    # writes below -- so the number answers "how long did the work take" rather
    # than "how busy was the event loop".
    started = time.perf_counter()
    try:
        # The agent is synchronous and makes several LLM calls, so it has to run
        # off the event loop or it stalls every other request for its duration.
        agent_result = await run_in_threadpool(
            run_agent,
            question=body.question,
            history=history,
            engine=engine,
            db_type=record["db_type"],
            database_name=record["database_name"],
        )
    except Exception as e:
        # Never f-string the provider's exception into the reply: its str() is
        # the raw JSON body it sent us, which belongs in the log and nowhere
        # near a chat bubble.
        failure = classify_model_failure(e)
        logfire.exception(
            "Agent failed ({error_type}): {hint}",
            error_type=type(e).__name__,
            hint=failure.operator_hint,
        )
        raise HTTPException(
            status_code=failure.status_code,
            detail={"code": failure.code, "message": failure.message},
        ) from e

    if not agent_result.get("valid") or agent_result.get("error"):
        error = agent_result.get("error", "Query generation failed")
        logfire.error("Agent failed: {error}", error=error)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "QUERY_ERROR", "message": error},
        )

    elapsed_ms = round((time.perf_counter() - started) * 1000)
    generated_query = agent_result.get("query")
    result_data = agent_result.get("result") or {}
    columns = result_data.get("columns", [])
    rows = result_data.get("rows", [])
    message = agent_result.get("message")

    # Persist only once the turn succeeded, so a failed question does not leave
    # an unanswered message poisoning the next turn's context.
    now = _now()
    if conversation is None:
        conversation_id = uuid.uuid4().hex
        conversation = {
            "connection_id": connection_id,
            "title": body.question[:255],
            "created_at": now,
            "updated_at": now,
        }
    else:
        # So "last active" ordering is right.
        conversation["updated_at"] = now

    # jsonable_encoder makes the snapshot storable: rows can hold Decimal, date,
    # and datetime values that a plain json.dumps would choke on. Only stored
    # when a query actually ran; a greeting or refusal has no result.
    result_snapshot = (
        jsonable_encoder({"columns": columns, "rows": rows, "row_count": len(rows)})
        if generated_query
        else None
    )

    pipe = redis.pipeline()
    pipe.hset(store.conversations_key(session.sid), conversation_id, json.dumps(conversation))
    pipe.rpush(
        store.messages_key(session.sid, conversation_id),
        json.dumps(
            {
                "id": uuid.uuid4().hex,
                "role": "user",
                "content": body.question,
                "sql_query": None,
                "result": None,
                "created_at": now,
            }
        ),
        json.dumps(
            {
                "id": uuid.uuid4().hex,
                "role": "assistant",
                "content": message or "",
                "sql_query": generated_query,
                "result": result_snapshot,
                "created_at": now,
                "elapsed_ms": elapsed_ms,
            }
        ),
    )
    await pipe.execute()
    # A conversation's message list is new on the first turn, so it has no
    # expiry until the session stamps its deadline onto it.
    await store.touch_expiry(redis, session)

    logfire.info(
        "Agent answered with {row_count} row(s) in {elapsed_ms}ms "
        "in conversation {conversation_id}",
        row_count=len(rows),
        elapsed_ms=elapsed_ms,
        conversation_id=conversation_id,
    )
    return NaturalLanguageQueryResponse(
        query=generated_query,
        columns=columns,
        rows=rows,
        row_count=len(rows),
        conversation_id=conversation_id,
        message=message,
        elapsed_ms=elapsed_ms,
    )


async def list_conversations(
    session: SessionData, connection_id: str, redis: Redis
) -> ConversationListResponse:
    """This connection's conversations, most recently active first."""
    records = await redis.hgetall(store.conversations_key(session.sid))
    mine = {}
    for cid, raw in records.items():
        record = json.loads(raw)
        if record["connection_id"] == connection_id:
            mine[cid] = record
    if not mine:
        return ConversationListResponse(conversations=[], total=0)

    # One round trip for the counts rather than one per conversation.
    pipe = redis.pipeline()
    for cid in mine:
        pipe.llen(store.messages_key(session.sid, cid))
    counts = await pipe.execute()

    summaries = sorted(
        (
            ConversationSummary(
                id=cid,
                title=record["title"],
                created_at=datetime.fromisoformat(record["created_at"]),
                updated_at=datetime.fromisoformat(record["updated_at"]),
                message_count=count,
            )
            for (cid, record), count in zip(mine.items(), counts, strict=True)
        ),
        key=lambda c: c.updated_at,
        reverse=True,
    )
    return ConversationListResponse(conversations=summaries, total=len(summaries))


async def get_conversation_detail(
    session: SessionData, connection_id: str, conversation_id: str, redis: Redis
) -> ConversationDetailResponse:
    """One conversation with its full message history, SQL and results intact."""
    record = await _load_conversation(session, connection_id, conversation_id, redis)
    messages = await _load_messages(session, conversation_id, redis)
    return ConversationDetailResponse(
        id=conversation_id,
        title=record["title"],
        created_at=datetime.fromisoformat(record["created_at"]),
        updated_at=datetime.fromisoformat(record["updated_at"]),
        messages=[MessageResponse(**m) for m in messages],
    )
