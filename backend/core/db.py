"""The app's own metadata database: engine, session factory, and the session
dependency.

This is infrastructure every package needs (auth, connections, conversations),
which is why it lives in core rather than inside any one of them.
"""
from __future__ import annotations

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import backend.core.config  # noqa: F401  -- loads backend/.env before DATABASE_URL is read


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


engine = create_async_engine(
    _async_url(os.environ["DATABASE_URL"]),
    pool_pre_ping=True,
    pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
