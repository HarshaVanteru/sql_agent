"""Connection management: attach a database to the current session."""
from __future__ import annotations

from fastapi import APIRouter, status

from app.session.deps import CurrentSession, RedisClient

from . import service
from .schemas import (
    ConnectionCreateRequest,
    ConnectionDetailResponse,
    ConnectionListResponse,
    ConnectionResponse,
)

router = APIRouter(prefix="/api/connections", tags=["Connections"])


@router.post("", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def add_connection(
    body: ConnectionCreateRequest, session: CurrentSession, redis: RedisClient
) -> ConnectionResponse:
    """Connect a database. Its credentials are checked before anything is stored."""
    return await service.create_connection_for_session(session, body, redis)


@router.get("", response_model=ConnectionListResponse)
async def list_connections(
    session: CurrentSession, redis: RedisClient
) -> ConnectionListResponse:
    """Every database connected in this session."""
    return await service.list_connections(session, redis)


@router.get("/{connection_id}", response_model=ConnectionDetailResponse)
async def get_connection(
    connection_id: str, session: CurrentSession, redis: RedisClient
) -> ConnectionDetailResponse:
    """One connection's details, without its password."""
    return await service.get_connection_detail(session, connection_id, redis)


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_connection(
    connection_id: str, session: CurrentSession, redis: RedisClient
) -> None:
    """Forget a connection and its conversations."""
    await service.delete_connection(session, connection_id, redis)
