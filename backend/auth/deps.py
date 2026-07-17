"""FastAPI dependencies: database session and the current user."""
from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import backend.core.config  # noqa: F401  -- loads backend/.env before DATABASE_URL is read
from backend.auth.models import User
from backend.auth.security import decode_access_token


def _async_url(url: str) -> str:
    """Normalise a DATABASE_URL to an async driver."""
    for sync_prefix, async_prefix in (
        ("postgresql+psycopg2://", "postgresql+asyncpg://"),
        ("postgresql://", "postgresql+asyncpg://"),
        ("mysql+pymysql://", "mysql+aiomysql://"),
        ("mysql://", "mysql+aiomysql://"),
    ):
        if url.startswith(sync_prefix):
            return url.replace(sync_prefix, async_prefix, 1)
    return url


_engine = create_async_engine(
    _async_url(os.environ["DATABASE_URL"]),
    pool_pre_ping=True,
    pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
)

AsyncSessionLocal = async_sessionmaker(_engine, expire_on_commit=False)

_bearer = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


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
