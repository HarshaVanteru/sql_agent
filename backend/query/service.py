"""Business logic for query execution."""
import logging
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Database
from backend.query.sql.pipeline import run_sql_pipeline
from backend.query.nosql.pipeline import run_nosql_pipeline
from backend.query.databases.mysql import create_mysql_connection, execute_mysql_query
from backend.query.databases.postgres import create_postgres_connection, execute_postgres_query
from backend.query.databases.mongodb import create_mongodb_connection, execute_mongodb_query
from .schemas import QueryRequest, QueryResponse, NaturalLanguageQueryRequest, NaturalLanguageQueryResponse

logger = logging.getLogger(__name__)

try:
    from langchain_groq import ChatGroq
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logger.warning("LangChain Groq not available - NL queries will be disabled")


async def execute_query(user_id: str, database_id: str, body: QueryRequest, db: AsyncSession) -> QueryResponse:
    """Execute a direct query against a user's database (SQL or NoSQL)."""
    logger.info(f"Executing query for user {user_id}, database {database_id}")

    # Get database and credentials (eager load credentials)
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
        logger.warning(f"Database {database_id} not found for user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Database not found"},
        )

    creds = database.credentials
    if not creds:
        logger.warning(f"Credentials missing for database {database_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "MISSING_CREDS", "message": "Database credentials missing"},
        )

    db_type = database.db_type.lower()

    if db_type == "mysql":
        engine = create_mysql_connection(creds.host, creds.port, creds.username, creds.password, creds.database_name)
        result_data = execute_mysql_query(engine, body.query)

    elif db_type == "postgresql":
        engine = create_postgres_connection(creds.host, creds.port, creds.username, creds.password, creds.database_name)
        result_data = execute_postgres_query(engine, body.query)

    elif db_type == "mongodb":
        client = create_mongodb_connection(creds.host, creds.port, creds.username, creds.password, creds.database_name)
        result_data = execute_mongodb_query(client, creds.database_name, body.query)

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "UNSUPPORTED_DB", "message": f"Database type '{database.db_type}' is not supported"},
        )

    return QueryResponse(
        columns=result_data["columns"],
        rows=result_data["rows"],
        row_count=result_data["row_count"],
    )


async def execute_natural_language_query(
    user_id: str, database_id: str, body: NaturalLanguageQueryRequest, db: AsyncSession
) -> NaturalLanguageQueryResponse:
    """Execute a natural language query using SQL or NoSQL pipelines."""
    if not LLM_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={"code": "LLM_NOT_AVAILABLE", "message": "LLM service is not configured"},
        )

    logger.info(f"Processing NL query for user {user_id}, database {database_id}")

    # Get database and credentials
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

    db_type = database.db_type.lower()

    try:
        if db_type == "mysql" or db_type == "postgresql":
            # Use SQL pipeline
            if db_type == "mysql":
                engine = create_mysql_connection(creds.host, creds.port, creds.username, creds.password, creds.database_name)
                logger.info(f"MySQL engine created for {creds.host}:{creds.port}/{creds.database_name}")
            else:
                engine = create_postgres_connection(creds.host, creds.port, creds.username, creds.password, creds.database_name)
                logger.info(f"PostgreSQL engine created for {creds.host}:{creds.port}/{creds.database_name}")

            logger.info(f"Running SQL pipeline for question: {body.question[:100]}...")
            pipeline_result = run_sql_pipeline(
                question=body.question,
                history=[],
                engine=engine,
                system_prompt=database.system_prompt,
                db_type=db_type,
                database_name=creds.database_name,
            )

            # Check if pipeline succeeded
            if not pipeline_result.get("valid") or pipeline_result.get("error"):
                logger.error(f"SQL Pipeline validation failed: {pipeline_result.get('error')}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "QUERY_ERROR", "message": pipeline_result.get("error", "Query generation failed")},
                )

            generated_query = pipeline_result.get("sql")
            result_data = pipeline_result.get("result", {})
            columns = result_data.get("columns", [])
            rows = result_data.get("rows", [])

            logger.info(f"SQL Pipeline executed successfully - returned {len(rows)} rows")
            logger.info(f"Generated SQL: {generated_query[:200] if generated_query else 'None'}")
            return NaturalLanguageQueryResponse(
                sql=generated_query,
                query_type="sql",
                columns=columns,
                rows=rows,
                row_count=len(rows),
            )

        elif db_type == "mongodb":
            # Use NoSQL pipeline
            client = create_mongodb_connection(creds.host, creds.port, creds.username, creds.password, creds.database_name)
            logger.info(f"MongoDB client created for {creds.host}:{creds.port}/{creds.database_name}")

            logger.info(f"Running NoSQL pipeline for question: {body.question[:100]}...")
            pipeline_result = run_nosql_pipeline(
                question=body.question,
                client=client,
                database_name=creds.database_name,
                history=[],
                system_prompt=database.system_prompt,
            )

            # Check if pipeline succeeded
            if not pipeline_result.get("valid") or pipeline_result.get("error"):
                logger.error(f"NoSQL Pipeline validation failed: {pipeline_result.get('error')}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "QUERY_ERROR", "message": pipeline_result.get("error", "Query generation failed")},
                )

            generated_query = pipeline_result.get("query")
            result_data = pipeline_result.get("result", {})
            columns = result_data.get("columns", [])
            rows = result_data.get("rows", [])

            logger.info(f"NoSQL Pipeline executed successfully - returned {len(rows)} rows")
            logger.info(f"Generated MongoDB Query: {generated_query[:200] if generated_query else 'None'}")
            return NaturalLanguageQueryResponse(
                query=generated_query,
                query_type="mongodb",
                columns=columns,
                rows=rows,
                row_count=len(rows),
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "UNSUPPORTED_DB", "message": f"Database type '{database.db_type}' is not supported"},
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Natural language query failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "QUERY_ERROR", "message": f"Query processing failed: {str(e)}"},
        )
