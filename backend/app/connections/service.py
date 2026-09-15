"""Connecting a database to a session, and reading those connections back.

A connection is stored under the session that made it and nowhere else, so it
disappears with the session. The password is Fernet-encrypted on the way in: a
visitor may well hand over a real production credential, and Redis is a shared
process.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import logfire
from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool
from redis.asyncio import Redis
from sqlalchemy import text

from app.core.crypto import decrypt, encrypt
from app.query.databases.connections import (
    SUPPORTED_DB_TYPES,
    connection_error_message,
    create_connection,
    dialect_label,
)
from app.session import store
from app.session.store import SessionData

from .schemas import (
    ConnectionCreateRequest,
    ConnectionCredentialOut,
    ConnectionDetailResponse,
    ConnectionListResponse,
    ConnectionResponse,
)


def _not_found(connection_id: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "NOT_FOUND", "message": f"Connection {connection_id} not found"},
    )


def _verify_credentials(
    db_type: str, host: str, port: int, username: str, password: str, database_name: str
) -> None:
    """Prove the credentials work by connecting and running SELECT 1.

    Synchronous and blocking, so callers run it in a threadpool. Failing here
    means the visitor finds out at connect time, with a message they can act on,
    rather than at the end of their first question.
    """
    db_type_lower = db_type.lower()
    if db_type_lower not in SUPPORTED_DB_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "UNSUPPORTED_DB_TYPE",
                "message": f"Unsupported database type: {db_type}. "
                f"Supported: {', '.join(sorted(SUPPORTED_DB_TYPES))}",
            },
        )

    label = dialect_label(db_type_lower)
    with logfire.span(
        "Validating {db_type} credentials for {host}:{port}/{database_name}",
        db_type=db_type,
        host=host,
        port=port,
        database_name=database_name,
    ):
        try:
            engine = create_connection(db_type, host, port, username, password, database_name)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except HTTPException:
            raise
        except Exception as e:
            error_msg = connection_error_message(db_type_lower, e, host, port)
            logfire.warning("{label} validation failed: {error}", label=label, error=error_msg)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_CREDENTIALS", "message": error_msg},
            )
        logfire.info(
            "{label} credentials validated for {host}:{port}/{database_name}",
            label=label,
            host=host,
            port=port,
            database_name=database_name,
        )


def _to_response(connection_id: str, record: dict) -> ConnectionResponse:
    return ConnectionResponse(
        id=connection_id,
        name=record["name"],
        db_type=record["db_type"],
        created_at=datetime.fromisoformat(record["created_at"]),
    )


async def create_connection_for_session(
    session: SessionData, body: ConnectionCreateRequest, redis: Redis
) -> ConnectionResponse:
    """Verify a database's credentials, then store it under this session."""
    key = store.connections_key(session.sid)

    existing = await redis.hgetall(key)
    if any(json.loads(v)["name"] == body.name for v in existing.values()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "CONNECTION_EXISTS",
                "message": f"A connection named '{body.name}' already exists",
            },
        )

    creds = body.credentials
    await run_in_threadpool(
        _verify_credentials,
        body.db_type,
        creds.host,
        creds.port,
        creds.username,
        creds.password,
        creds.database_name,
    )

    connection_id = uuid.uuid4().hex
    record = {
        "name": body.name,
        "db_type": body.db_type.lower(),
        "host": creds.host,
        "port": creds.port,
        "username": creds.username,
        "password": encrypt(creds.password),
        "database_name": creds.database_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await redis.hset(key, connection_id, json.dumps(record))
    # The hash may have just been created, which gives it no expiry of its own.
    await store.touch_expiry(redis, session)

    logfire.info(
        "Connection {connection_id} ({db_type}) added to session {session_id}",
        connection_id=connection_id,
        db_type=record["db_type"],
        session_id=session.sid,
    )
    return _to_response(connection_id, record)


async def get_record(session: SessionData, connection_id: str, redis: Redis) -> dict:
    """The raw stored connection, password still encrypted. 404 if it is gone."""
    raw = await redis.hget(store.connections_key(session.sid), connection_id)
    if raw is None:
        raise _not_found(connection_id)
    return json.loads(raw)


def record_password(record: dict) -> str:
    """Decrypt a stored connection password, or fail cleanly."""
    try:
        return decrypt(record["password"])
    except ValueError as e:
        logfire.error("Could not decrypt stored credentials: {error}", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "CREDENTIALS_ERROR",
                "message": "Stored credentials could not be read. Reconnect the database.",
            },
        )


async def list_connections(session: SessionData, redis: Redis) -> ConnectionListResponse:
    """This session's connections, newest first."""
    records = await redis.hgetall(store.connections_key(session.sid))
    connections = sorted(
        (_to_response(cid, json.loads(raw)) for cid, raw in records.items()),
        key=lambda c: c.created_at,
        reverse=True,
    )
    return ConnectionListResponse(connections=connections, total=len(connections))


async def get_connection_detail(
    session: SessionData, connection_id: str, redis: Redis
) -> ConnectionDetailResponse:
    """One connection, with its host/port/user but never its password."""
    record = await get_record(session, connection_id, redis)
    return ConnectionDetailResponse(
        **_to_response(connection_id, record).model_dump(),
        credentials=ConnectionCredentialOut(
            host=record["host"],
            port=record["port"],
            username=record["username"],
            database_name=record["database_name"],
        ),
    )


async def delete_connection(session: SessionData, connection_id: str, redis: Redis) -> None:
    """Forget a connection and every conversation held against it."""
    removed = await redis.hdel(store.connections_key(session.sid), connection_id)
    if not removed:
        raise _not_found(connection_id)

    # Conversations are keyed to a connection; leaving them behind would show
    # history for a database the visitor can no longer reach.
    conversations = await redis.hgetall(store.conversations_key(session.sid))
    stale = [
        cid
        for cid, raw in conversations.items()
        if json.loads(raw)["connection_id"] == connection_id
    ]
    if stale:
        pipe = redis.pipeline()
        pipe.hdel(store.conversations_key(session.sid), *stale)
        for cid in stale:
            pipe.delete(store.messages_key(session.sid, cid))
        await pipe.execute()

    logfire.info(
        "Connection {connection_id} deleted with {conversations} conversation(s)",
        connection_id=connection_id,
        conversations=len(stale),
    )
