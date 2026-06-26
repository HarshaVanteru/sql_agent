"""Business logic for database management."""
import uuid
import logging
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Database, DatabaseCredential
from backend.query.prompts import get_default_prompt
from .schemas import (
    DatabaseCreateRequest, DatabaseResponse, DatabaseDetailResponse,
    DatabaseCredentialInput
)

logger = logging.getLogger(__name__)


async def create_database(
    user_id: str,
    body: DatabaseCreateRequest,
    db: AsyncSession,
) -> DatabaseResponse:
    """Create a new database and its credentials."""

    # Check if database with same name exists for user
    existing = await db.execute(
        select(Database).where(
            Database.user_id == user_id,
            Database.name == body.name,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "DB_EXISTS", "message": f"Database '{body.name}' already exists"},
        )

    # Generate ID and timestamp
    db_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    # Get default prompt for the database type
    try:
        default_prompt = get_default_prompt(body.db_type)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "UNSUPPORTED_DB_TYPE", "message": str(e)},
        )

    # Create database
    database = Database(
        id=db_id,
        user_id=user_id,
        name=body.name,
        db_type=body.db_type,
        system_prompt=default_prompt,
        created_at=now,
        updated_at=now,
    )
    db.add(database)
    await db.flush()

    # Create credentials
    credentials = DatabaseCredential(
        database_id=db_id,
        host=body.credentials.host,
        port=body.credentials.port,
        username=body.credentials.username,
        password=body.credentials.password,
        database_name=body.credentials.database_name,
    )
    db.add(credentials)
    await db.commit()

    # Build response from local variables (not database object)
    return DatabaseResponse(
        id=db_id,
        name=body.name,
        db_type=body.db_type,
        created_at=now.isoformat(),
    )


async def get_databases(user_id: str, db: AsyncSession) -> list[DatabaseResponse]:
    """Get all databases for a user."""
    result = await db.execute(
        select(Database).where(Database.user_id == user_id).order_by(Database.created_at.desc())
    )
    databases = result.scalars().all()

    responses = []
    for d in databases:
        responses.append(
            DatabaseResponse(
                id=d.id,
                name=d.name,
                db_type=d.db_type,
                created_at=d.created_at.isoformat() if d.created_at else "",
            )
        )
    return responses


async def get_database_detail(user_id: str, database_id: str, db: AsyncSession) -> DatabaseDetailResponse:
    """Get database with credentials."""
    result = await db.execute(
        select(Database).where(
            Database.id == database_id,
            Database.user_id == user_id,
        )
    )
    database = result.scalar_one_or_none()
    if not database:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Database not found"},
        )

    creds = database.credentials
    if not creds:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "MISSING_CREDS", "message": "Database credentials missing"},
        )

    return DatabaseDetailResponse(
        id=database.id,
        name=database.name,
        db_type=database.db_type,
        created_at=database.created_at.isoformat() if database.created_at else "",
        credentials=DatabaseCredentialInput(
            host=creds.host,
            port=creds.port,
            username=creds.username,
            password=creds.password,
            database_name=creds.database_name,
        ),
    )


async def delete_database(user_id: str, database_id: str, db: AsyncSession) -> dict:
    """Delete a database and its credentials."""
    result = await db.execute(
        select(Database).where(
            Database.id == database_id,
            Database.user_id == user_id,
        )
    )
    database = result.scalar_one_or_none()
    if not database:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Database not found"},
        )

    await db.delete(database)
    await db.commit()

    return {"message": "Database deleted successfully"}
