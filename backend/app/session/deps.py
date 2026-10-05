"""The session dependency every protected endpoint hangs off.

There is no login: whoever holds the signed cookie is whoever started that
session. The cookie carries only the id (Starlette's SessionMiddleware signs it
with SECRET_KEY); the session itself lives in Redis, so it expires server-side
whatever the browser decides to keep.
"""
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis  # type: ignore

from app.session import store
from app.session.store import SessionData


async def get_redis(request: Request) -> Redis:
    """The client opened once in the app lifespan."""
    return request.app.state.redis


async def get_session(
    request: Request, redis: Annotated[Redis, Depends(get_redis)]
) -> SessionData:
    """Resolve the current session, or refuse the request.

    A missing cookie and an expired session are the same answer on purpose: in
    both cases the caller needs to start a new session, and saying which one it
    was tells an unauthenticated caller whether a session id exists.
    """
    sid = request.session.get("sid")
    session = await store.get(redis, sid) if sid else None
    if session is None:
        # Clear the stale cookie so the browser stops presenting it.
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "NO_SESSION",
                "message": "No active session. Start one to continue.",
            },
        )
    return session


CurrentSession = Annotated[SessionData, Depends(get_session)]
RedisClient = Annotated[Redis, Depends(get_redis)]
