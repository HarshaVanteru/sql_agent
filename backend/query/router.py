"""Query execution router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.deps import get_current_user, get_db
from backend.auth.models import User
from .schemas import QueryRequest, QueryResponse, NaturalLanguageQueryRequest, NaturalLanguageQueryResponse
from .service import execute_query, execute_natural_language_query

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
