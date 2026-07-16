"""Business logic for query execution."""
import logging
import os

from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Database
from backend.query.agent.loop import run_agent
from backend.query.models import Conversation, Message
from backend.query.databases.mysql import create_mysql_connection, execute_mysql_query
from backend.query.databases.postgres import create_postgres_connection, execute_postgres_query
from .schemas import QueryRequest, QueryResponse, NaturalLanguageQueryRequest, NaturalLanguageQueryResponse

logger = logging.getLogger(__name__)

# Turns replayed to the agent. Each turn is a question plus the SQL answering it,
# so this bounds how much of a long conversation reaches the prompt.
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))


async def _load_conversation(
    user_id: str, database_id: str, conversation_id: str, db: AsyncSession
) -> Conversation:
    """Fetch a conversation with its messages, scoped to this user and database."""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
            Conversation.database_id == database_id,
        )
    )
    conversation = result.unique().scalar_one_or_none()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Conversation not found"},
        )
    return conversation


def _to_agent_history(messages: list[Message]) -> list:
    """Convert stored messages into the message objects the agent expects."""
    recent = messages[-MAX_HISTORY_MESSAGES:]
    return [
        HumanMessage(content=m.content) if m.role == "user" else AIMessage(content=m.content)
        for m in recent
    ]


async def execute_query(user_id: str, database_id: str, body: QueryRequest, db: AsyncSession) -> QueryResponse:
    """Execute a direct query against a user's database."""
    logger.info(f"Executing query for user {user_id}, database {database_id}")

    # Get database and credentials (eager load credentials)
    result = await db.execute(
        select(Database)
        .options(selectinload(Database.credentials))
        .where(
            Database.id == database_id,
            Database.user_id == user_id,
        )
    )
    database = result.unique().scalar_one_or_none()
    if not database:
        logger.warning(f"Database {database_id} not found for user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Database not found"},
        )

    creds = database.credentials
    if not creds:
        logger.warning(f"Credentials missing for database {database_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "MISSING_CREDS", "message": "Database credentials missing"},
        )

    db_type = database.db_type.lower()

    if db_type == "mysql":
        engine = create_mysql_connection(creds.host, creds.port, creds.username, creds.password, creds.database_name)
        result_data = await run_in_threadpool(execute_mysql_query, engine, body.query)

    elif db_type == "postgresql":
        engine = create_postgres_connection(creds.host, creds.port, creds.username, creds.password, creds.database_name)
        result_data = await run_in_threadpool(execute_postgres_query, engine, body.query)

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "UNSUPPORTED_DB", "message": f"Database type '{database.db_type}' is not supported"},
        )

    return QueryResponse(
        columns=result_data["columns"],
        rows=result_data["rows"],
        row_count=result_data["row_count"],
    )


async def execute_natural_language_query(
    user_id: str, database_id: str, body: NaturalLanguageQueryRequest, db: AsyncSession
) -> NaturalLanguageQueryResponse:
    """Answer a natural language question with the SQL agent, in conversation context."""
    logger.info(f"Processing NL query for user {user_id}, database {database_id}")

    # Get database and credentials
    result = await db.execute(
        select(Database)
        .options(selectinload(Database.credentials))
        .where(
            Database.id == database_id,
            Database.user_id == user_id,
        )
    )
    database = result.unique().scalar_one_or_none()
    if not database:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Database not found"},
        )

    creds = database.credentials
    if not creds:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "MISSING_CREDS", "message": "Database credentials missing"},
        )

    db_type = database.db_type.lower()

    if db_type == "mysql":
        engine = create_mysql_connection(creds.host, creds.port, creds.username, creds.password, creds.database_name)
    elif db_type == "postgresql":
        engine = create_postgres_connection(creds.host, creds.port, creds.username, creds.password, creds.database_name)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "UNSUPPORTED_DB", "message": f"Database type '{database.db_type}' is not supported"},
        )

    conversation = None
    history = []
    if body.conversation_id:
        conversation = await _load_conversation(user_id, database_id, body.conversation_id, db)
        history = _to_agent_history(conversation.messages)
        logger.info(f"Continuing conversation {conversation.id} with {len(history)} prior message(s)")

    try:
        # The agent is synchronous and makes several LLM calls, so it has to run
        # off the event loop or it stalls every other request for its duration.
        agent_result = await run_in_threadpool(
            run_agent,
            question=body.question,
            history=history,
            engine=engine,
            db_type=db_type,
            database_name=creds.database_name,
        )
    except Exception as e:
        logger.error(f"Natural language query failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "QUERY_ERROR", "message": f"Query processing failed: {str(e)}"},
        )

    if not agent_result.get("valid") or agent_result.get("error"):
        error = agent_result.get("error", "Query generation failed")
        logger.error(f"Agent failed: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "QUERY_ERROR", "message": error},
        )

    generated_query = agent_result.get("query")
    result_data = agent_result.get("result") or {}
    columns = result_data.get("columns", [])
    rows = result_data.get("rows", [])
    message = agent_result.get("message")

    # Persist only once the turn succeeded, so a failed question does not leave
    # an unanswered message poisoning the next turn's context.
    if conversation is None:
        conversation = Conversation(
            user_id=user_id,
            database_id=database_id,
            title=body.question[:255],
        )
        db.add(conversation)
        await db.flush()

    # Added by foreign key rather than through conversation.messages: appending
    # to the collection would lazy-load it, and async SQLAlchemy cannot emit IO
    # from attribute access.
    db.add(Message(conversation_id=conversation.id, role="user", content=body.question))
    db.add(Message(
        conversation_id=conversation.id,
        role="assistant",
        content=generated_query or message or "",
    ))
    await db.commit()

    logger.info(f"Agent answered with {len(rows)} row(s) in conversation {conversation.id}")
    return NaturalLanguageQueryResponse(
        query=generated_query,
        columns=columns,
        rows=rows,
        row_count=len(rows),
        conversation_id=conversation.id,
        message=message,
    )
