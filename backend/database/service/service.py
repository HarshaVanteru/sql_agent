"""Business logic for database management."""
import uuid
from datetime import datetime, timezone

import logfire
from fastapi import HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.crypto import encrypt
from backend.database.models import Database, DatabaseCredential
from backend.query.databases.mysql import create_mysql_connection
from backend.query.databases.postgres import create_postgres_connection
from ..schemas import (
    DatabaseCreateRequest, DatabaseResponse, DatabaseDetailResponse,
    DatabaseCredentialOut
)


def _parse_mysql_error(error: Exception) -> str:
    """Extract user-friendly error message from MySQL errors."""
    error_str = str(error).lower()

    if "access denied" in error_str or "1045" in error_str:
        return "Invalid username or password"
    elif "unknown database" in error_str or "1049" in error_str:
        return f"Database does not exist"
    elif "can't connect" in error_str or "2003" in error_str or "connection refused" in error_str:
        return f"Cannot connect to MySQL server at {error_str.split('on')[1].split('(')[0].strip() if 'on' in error_str else 'the specified host'}"
    elif "getaddrinfo failed" in error_str or "11001" in error_str:
        return "Invalid hostname - cannot resolve address"
    elif "connection timeout" in error_str:
        return "Connection timeout - server not responding"
    else:
        return f"Connection failed: {str(error).split('(')[0].strip()}"


def _parse_postgres_error(error: Exception) -> str:
    """Extract user-friendly error message from PostgreSQL errors."""
    error_str = str(error).lower()

    if "password authentication failed" in error_str:
        return "Invalid username or password"
    elif "database" in error_str and "does not exist" in error_str:
        return "Database does not exist"
    elif "could not translate" in error_str or "unknown host" in error_str:
        return "Invalid hostname - cannot resolve address"
    elif "connection refused" in error_str:
        return f"Cannot connect to PostgreSQL server - connection refused"
    elif "timeout" in error_str:
        return "Connection timeout - server not responding"
    else:
        return f"Connection failed: {str(error).split('(')[0].strip()}"


async def validate_database_credentials(db_type: str, host: str, port: int, username: str, password: str, database_name: str) -> None:
    """Validate database credentials by attempting to connect and run a test query.

    Raises HTTPException if credentials are invalid.
    """
    db_type_lower = db_type.lower()

    with logfire.span(
        "Validating {db_type} credentials for {host}:{port}/{database_name}",
        db_type=db_type,
        host=host,
        port=port,
        database_name=database_name,
    ):
        if db_type_lower == "mysql":
            try:
                engine = create_mysql_connection(host, port, username, password, database_name)
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logfire.info(
                    "MySQL credentials validated for {host}:{port}/{database_name}",
                    host=host,
                    port=port,
                    database_name=database_name,
                )
            except Exception as e:
                error_msg = _parse_mysql_error(e)
                logfire.warning("MySQL validation failed: {error}", error=error_msg)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "INVALID_CREDENTIALS", "message": error_msg},
                )

        elif db_type_lower == "postgresql":
            try:
                engine = create_postgres_connection(host, port, username, password, database_name)
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logfire.info(
                    "PostgreSQL credentials validated for {host}:{port}/{database_name}",
                    host=host,
                    port=port,
                    database_name=database_name,
                )
            except Exception as e:
                error_msg = _parse_postgres_error(e)
                logfire.warning("PostgreSQL validation failed: {error}", error=error_msg)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "INVALID_CREDENTIALS", "message": error_msg},
                )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "UNSUPPORTED_DB_TYPE", "message": f"Unsupported database type: {db_type}"},
            )


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

    # Validate credentials before saving
    await validate_database_credentials(
        body.db_type,
        body.credentials.host,
        body.credentials.port,
        body.credentials.username,
        body.credentials.password,
        body.credentials.database_name,
    )

    # Generate ID and timestamp
    db_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    # Create database
    database = Database(
        id=db_id,
        user_id=user_id,
        name=body.name,
        db_type=body.db_type,
        created_at=now,
        updated_at=now,
    )
    db.add(database)
    await db.flush()

    # Create credentials. The password is encrypted at rest; everything else is
    # not secret and stays queryable.
    credentials = DatabaseCredential(
        database_id=db_id,
        host=body.credentials.host,
        port=body.credentials.port,
        username=body.credentials.username,
        password=encrypt(body.credentials.password),
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
    """Get database with credentials, minus the password."""
    result = await db.execute(
        select(Database)
        .options(selectinload(Database.credentials))
        .where(
            Database.id == database_id,
            Database.user_id == user_id,
        )
    )
    database = result.unique().scalar_one_or_none()
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
        credentials=DatabaseCredentialOut(
            host=creds.host,
            port=creds.port,
            username=creds.username,
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
