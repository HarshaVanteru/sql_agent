"""MySQL database connection and query execution."""
import logging
from urllib.parse import quote_plus
from sqlalchemy import text
from fastapi import HTTPException, status

from backend.query.databases.engines import get_engine

logger = logging.getLogger(__name__)


def create_mysql_connection(host: str, port: int, username: str, password: str, database_name: str):
    """Create a MySQL database engine."""
    try:
        encoded_user = quote_plus(username)
        encoded_password = quote_plus(password)
        db_url = f"mysql+pymysql://{encoded_user}:{encoded_password}@{host}:{port}/{database_name}"
        logger.debug(f"MySQL connection URL: mysql+pymysql://{username}:***@{host}:{port}/{database_name}")
        return get_engine(db_url)
    except Exception as e:
        logger.error(f"Failed to create MySQL connection: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CONNECTION_ERROR", "message": f"Failed to connect to MySQL: {str(e)}"},
        )


def execute_mysql_query(engine, query: str) -> dict:
    """Execute a query against MySQL database."""
    try:
        logger.info(f"Executing MySQL query: {query[:100]}...")
        with engine.connect() as conn:
            query_result = conn.execute(text(query))
            columns = list(query_result.keys())
            rows = [dict(zip(columns, row)) for row in query_result.fetchall()]

        logger.info(f"MySQL query executed successfully - returned {len(rows)} rows")
        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
        }
    except Exception as e:
        logger.error(f"MySQL query execution failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "QUERY_ERROR", "message": f"Query execution failed: {str(e)}"},
        )


def get_mysql_schema(engine) -> str:
    """Fetch schema from MySQL database."""
    try:
        with engine.connect() as conn:
            # Get table structure
            result = conn.execute(text("""
                SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, DATA_TYPE
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                ORDER BY TABLE_NAME, ORDINAL_POSITION
            """))

            schema = {}
            for table, column, col_type, data_type in result:
                if table not in schema:
                    schema[table] = []
                display_type = col_type if data_type == "enum" else data_type
                schema[table].append(f"{column} ({display_type})")

            # Get foreign keys
            fk_result = conn.execute(text("""
                SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = DATABASE()
                AND REFERENCED_TABLE_NAME IS NOT NULL
            """))

            fks = [
                f"  {table}.{col} → {ref_table}.{ref_col}"
                for table, col, ref_table, ref_col in fk_result
            ]

            schema_str = "\n".join(
                f"Table: {table}\n" + "\n".join(f"  - {c}" for c in cols)
                for table, cols in sorted(schema.items())
            )

            if fks:
                schema_str += "\n\nForeign Keys:\n" + "\n".join(fks)

            return schema_str

    except Exception as e:
        logger.error(f"Failed to fetch MySQL schema: {str(e)}", exc_info=True)
        raise
