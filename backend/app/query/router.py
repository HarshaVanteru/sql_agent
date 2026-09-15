"""Asking questions of a connected database, and reading back what was asked."""
from __future__ import annotations

from fastapi import APIRouter

from app.session.deps import CurrentSession, RedisClient

from . import service
from .schemas import (
    ConversationDetailResponse,
    ConversationListResponse,
    NaturalLanguageQueryRequest,
    NaturalLanguageQueryResponse,
)

router = APIRouter(prefix="/api/connections", tags=["Queries"])


@router.post("/{connection_id}/natural-query", response_model=NaturalLanguageQueryResponse)
async def ask_question(
    connection_id: str,
    body: NaturalLanguageQueryRequest,
    session: CurrentSession,
    redis: RedisClient,
) -> NaturalLanguageQueryResponse:
    """Ask a question in plain English. The agent writes and runs the SQL."""
    return await service.ask(session, connection_id, body, redis)


@router.get("/{connection_id}/conversations", response_model=ConversationListResponse)
async def get_conversations(
    connection_id: str, session: CurrentSession, redis: RedisClient
) -> ConversationListResponse:
    """This connection's conversations, most recently active first."""
    return await service.list_conversations(session, connection_id, redis)


@router.get(
    "/{connection_id}/conversations/{conversation_id}",
    response_model=ConversationDetailResponse,
)
async def get_conversation(
    connection_id: str,
    conversation_id: str,
    session: CurrentSession,
    redis: RedisClient,
) -> ConversationDetailResponse:
    """A single conversation, replayed with its SQL and results."""
    return await service.get_conversation_detail(session, connection_id, conversation_id, redis)
