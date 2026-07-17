"""FastAPI dependency: the current user.

The database session dependency lives in backend.core.db -- it is infrastructure
rather than an auth concern.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.models import User
from backend.auth.security import decode_access_token
from backend.core.db import get_db

_bearer = HTTPBearer(auto_error=False)


def _unauthorized(code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": code, "message": message},
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if not credentials:
        raise _unauthorized("INVALID_TOKEN", "Authorization header required")

    try:
        user_id = decode_access_token(credentials.credentials)
    except ValueError as exc:
        if str(exc) == "expired":
            raise _unauthorized("TOKEN_EXPIRED", "Access token has expired")
        raise _unauthorized("INVALID_TOKEN", "Invalid access token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise _unauthorized("INVALID_TOKEN", "User not found or inactive")

    return user
