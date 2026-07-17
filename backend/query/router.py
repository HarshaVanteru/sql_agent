"""Query execution router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.deps import get_current_user, get_db
from backend.auth.models import User
from .schemas import (
    QueryRequest,
    QueryResponse,
    NaturalLanguageQueryRequest,
    NaturalLanguageQueryResponse,
    ConversationListResponse,
    ConversationDetailResponse,
)
from .service import (
    execute_query,
    execute_natural_language_query,
    list_conversations,
    get_conversation_detail,
)

router = APIRouter(prefix="/api/databases", tags=["Queries"])


@router.post("/{database_id}/query", response_model=QueryResponse)
async def query_database(
    database_id: str,
    body: QueryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> QueryResponse:
    """Execute a query against a database."""
    return await execute_query(str(current_user.id), database_id, body, db)


@router.post("/{database_id}/natural-query", response_model=NaturalLanguageQueryResponse)
async def query_natural_language(
    database_id: str,
    body: NaturalLanguageQueryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NaturalLanguageQueryResponse:
    """Execute a natural language query (converts to SQL using LLM).

    Supports:
    - MySQL & PostgreSQL: Converts to SQL
    """
    return await execute_natural_language_query(str(current_user.id), database_id, body, db)


@router.get("/{database_id}/conversations", response_model=ConversationListResponse)
async def get_conversations(
    database_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConversationListResponse:
    """List this database's conversations, most recently active first."""
    return await list_conversations(str(current_user.id), database_id, db)


@router.get(
    "/{database_id}/conversations/{conversation_id}",
    response_model=ConversationDetailResponse,
)
async def get_conversation(
    database_id: str,
    conversation_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConversationDetailResponse:
    """Return a single conversation with its full message history."""
    return await get_conversation_detail(str(current_user.id), database_id, conversation_id, db)
