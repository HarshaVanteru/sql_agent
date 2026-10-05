"""Session router: start a visit, check it, extend it, end it."""
from __future__ import annotations

import logfire
from fastapi import APIRouter, HTTPException, Request, status

from app.session import store
from app.session.deps import CurrentSession, RedisClient
from app.session.schemas import SessionCreateRequest, SessionExtendRequest, SessionResponse

router = APIRouter(prefix="/api/session", tags=["Session"])


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def start_session(
    request: Request, body: SessionCreateRequest, redis: RedisClient
) -> SessionResponse:
    """Start a session from a name, and hand back the signed cookie that carries it."""
    session = await store.create(redis, body.name)
    request.session["sid"] = session.sid
    logfire.info(
        "Session {session_id} started for {name}", session_id=session.sid, name=session.name
    )
    return SessionResponse(
        session_id=session.sid,
        name=session.name,
        created_at=session.created_at,
        expires_at=session.expires_at,
    )


@router.get("", response_model=SessionResponse)
async def current_session(session: CurrentSession, redis: RedisClient) -> SessionResponse:
    """Who the caller is and how much they have connected, for page load."""
    return SessionResponse(
        session_id=session.sid,
        name=session.name,
        created_at=session.created_at,
        expires_at=session.expires_at,
        connection_count=await redis.hlen(store.connections_key(session.sid)),
    )


@router.post("/extend", response_model=SessionResponse)
async def extend_session(
    body: SessionExtendRequest, session: CurrentSession, redis: RedisClient
) -> SessionResponse:
    """Give a live session more time: 24 hours, 7 days or 30 days on top of what is left."""
    try:
        extended = await store.extend(redis, session, body.duration)
    except store.SessionAtMaximum:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "SESSION_AT_MAX",
                "message": "This session already has the maximum 30 days left.",
            },
        ) from None
    except store.SessionGone:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "NO_SESSION", "message": "That session has ended."},
        ) from None

    logfire.info(
        "Session {session_id} extended by {duration} to {expires_at}",
        session_id=extended.sid,
        duration=body.duration,
        expires_at=extended.expires_at.isoformat(),
    )
    return SessionResponse(
        session_id=extended.sid,
        name=extended.name,
        created_at=extended.created_at,
        expires_at=extended.expires_at,
        connection_count=await redis.hlen(store.connections_key(extended.sid)),
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def end_session(request: Request, session: CurrentSession, redis: RedisClient) -> None:
    """End the session now rather than waiting for it to expire."""
    await store.destroy(redis, session.sid)
    request.session.clear()
    logfire.info("Session {session_id} ended", session_id=session.sid)
