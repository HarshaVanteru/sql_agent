"""PostgreSQL database connection and query execution."""
import logging
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


def create_postgres_connection(host: str, port: int, username: str, password: str, database_name: str):
    """Create a PostgreSQL database engine."""
    try:
        encoded_user = quote_plus(username)
        encoded_password = quote_plus(password)
        db_url = f"postgresql+psycopg2://{encoded_user}:{encoded_password}@{host}:{port}/{database_name}"
        logger.debug(f"PostgreSQL connection URL: postgresql+psycopg2://{username}:***@{host}:{port}/{database_name}")
        engine = create_engine(db_url, echo=False)
        return engine
    except Exception as e:
        logger.error(f"Failed to create PostgreSQL connection: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CONNECTION_ERROR", "message": f"Failed to connect to PostgreSQL: {str(e)}"},
        )


def execute_postgres_query(engine, query: str) -> dict:
    """Execute a query against PostgreSQL database."""
    try:
        logger.info(f"Executing PostgreSQL query: {query[:100]}...")
        with engine.connect() as conn:
            query_result = conn.execute(text(query))
            columns = list(query_result.keys())
            rows = [dict(zip(columns, row)) for row in query_result.fetchall()]

        logger.info(f"PostgreSQL query executed successfully - returned {len(rows)} rows")
        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
        }
    except Exception as e:
        logger.error(f"PostgreSQL query execution failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "QUERY_ERROR", "message": f"Query execution failed: {str(e)}"},
        )


def get_postgres_schema(engine) -> str:
    """Fetch schema from PostgreSQL database."""
    try:
        with engine.connect() as conn:
            # Get table structure
            result = conn.execute(text("""
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
            """))

            schema = {}
            for table, column, data_type in result:
                if table not in schema:
                    schema[table] = []
                schema[table].append(f"{column} ({data_type})")

            # Get foreign keys
            fk_result = conn.execute(text("""
                SELECT
                    constraint_name,
                    table_name,
                    column_name,
                    referenced_table_name,
                    referenced_column_name
                FROM information_schema.referential_constraints
                JOIN information_schema.key_column_usage USING (constraint_catalog, constraint_schema, constraint_name)
                WHERE constraint_schema = 'public'
            """))

            fks = [
                f"  {table}.{col} → {ref_table}.{ref_col}"
                for _, table, col, ref_table, ref_col in fk_result
            ]

            schema_str = "\n".join(
                f"Table: {table}\n" + "\n".join(f"  - {c}" for c in cols)
                for table, cols in sorted(schema.items())
            )

            if fks:
                schema_str += "\n\nForeign Keys:\n" + "\n".join(fks)

            return schema_str

    except Exception as e:
        logger.error(f"Failed to fetch PostgreSQL schema: {str(e)}", exc_info=True)
        raise
