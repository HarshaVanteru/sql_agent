"""PostgreSQL database connection and query execution."""
from urllib.parse import quote_plus

import logfire
from sqlalchemy import text
from fastapi import HTTPException, status

from backend.query.databases.engines import get_engine


def create_postgres_connection(host: str, port: int, username: str, password: str, database_name: str):
    """Create a PostgreSQL database engine."""
    try:
        encoded_user = quote_plus(username)
        encoded_password = quote_plus(password)
        db_url = f"postgresql+psycopg2://{encoded_user}:{encoded_password}@{host}:{port}/{database_name}"
        logfire.debug(
            "PostgreSQL connection URL: postgresql+psycopg2://{username}:***@{host}:{port}/{database_name}",
            username=username,
            host=host,
            port=port,
            database_name=database_name,
        )
        return get_engine(db_url)
    except Exception as e:
        logfire.exception("Failed to create PostgreSQL connection: {error}", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CONNECTION_ERROR", "message": f"Failed to connect to PostgreSQL: {str(e)}"},
        )


def execute_postgres_query(engine, query: str) -> dict:
    """Execute a query against PostgreSQL database."""
    try:
        with logfire.span("Executing PostgreSQL query: {query_preview}...", query_preview=query[:100]):
            with engine.connect() as conn:
                query_result = conn.execute(text(query))
                columns = list(query_result.keys())
                rows = [dict(zip(columns, row)) for row in query_result.fetchall()]

            logfire.info(
                "PostgreSQL query executed successfully - returned {row_count} rows",
                row_count=len(rows),
            )
            return {
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
            }
    except Exception as e:
        logfire.exception("PostgreSQL query execution failed: {error}", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "QUERY_ERROR", "message": f"Query execution failed: {str(e)}"},
        )
