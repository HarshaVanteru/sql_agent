"""Database management router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth._core import get_current_user, get_db
from backend.auth.models import User
from .schemas import (
    DatabaseCreateRequest, DatabaseResponse, DatabaseListResponse, DatabaseDetailResponse
)
from .service import (
    create_database, get_databases, get_database_detail, delete_database
)

router = APIRouter(prefix="/api/databases", tags=["Databases"])


@router.post("", response_model=DatabaseResponse, status_code=201)
async def create_db(
    body: DatabaseCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DatabaseResponse:
    """Create a new database with credentials."""
    return await create_database(str(current_user.id), body, db)


@router.get("", response_model=DatabaseListResponse)
async def list_databases(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DatabaseListResponse:
    """Get all databases for current user."""
    databases = await get_databases(str(current_user.id), db)
    return DatabaseListResponse(databases=databases, total=len(databases))


@router.get("/{database_id}", response_model=DatabaseDetailResponse)
async def get_db_detail(
    database_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DatabaseDetailResponse:
    """Get database with credentials."""
    return await get_database_detail(str(current_user.id), database_id, db)


@router.delete("/{database_id}")
async def delete_db(
    database_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Delete a database."""
    return await delete_database(str(current_user.id), database_id, db)
