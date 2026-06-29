import logging
from langchain_groq import ChatGroq
from sqlalchemy import text
from dotenv import load_dotenv
from backend.query.prompts import get_default_prompt

load_dotenv()

logger = logging.getLogger(__name__)
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)

def _get_schema_from_engine(engine, database_name: str = None):
    """Fetch database schema from an engine (MySQL and PostgreSQL compatible)."""
    try:
        with engine.connect() as conn:
            dialect = engine.dialect.name

            if dialect == "mysql":
                # MySQL schema query
                if not database_name:
                    db_result = conn.execute(text("SELECT DATABASE()"))
                    database_name = db_result.scalar() or "unknown"

                cols_result = conn.execute(text("""
                    SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                    ORDER BY TABLE_NAME, ORDINAL_POSITION
                """))

                schema = {}
                for table, column, data_type in cols_result:
                    if table not in schema:
                        schema[table] = []
                    schema[table].append(f"{column} ({data_type})")

            elif dialect == "postgresql":
                # PostgreSQL schema query
                if not database_name:
                    db_result = conn.execute(text("SELECT current_database()"))
                    database_name = db_result.scalar() or "unknown"

                cols_result = conn.execute(text("""
                    SELECT table_name, column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    ORDER BY table_name, ordinal_position
                """))

                schema = {}
                for table, column, data_type in cols_result:
                    if table not in schema:
                        schema[table] = []
                    schema[table].append(f"{column} ({data_type})")
            else:
                return f"Database type '{dialect}' not fully supported"

            schema_str = f"Database: {database_name}\n\n"
            schema_str += "\n".join(
                f"Table: {table}\n" + "\n".join(f"  - {c}" for c in cols)
                for table, cols in sorted(schema.items())
            )

            return schema_str
    except Exception as e:
        logger.error(f"Error fetching schema: {str(e)}")
        raise

def generation_agent(state: dict) -> dict:
    connection = state.get("connection")
    if not connection:
        state["query"] = None
        state["error"] = "Database connection not provided"
        return state

    try:
        database_name = state.get("database_name")
        schema = _get_schema_from_engine(connection, database_name)

        # Get system prompt from state (stored in database)
        system_prompt = state.get("system_prompt")

        # If system_prompt is None (old databases), use default based on db_type
        if not system_prompt:
            db_type = state.get("db_type", "mysql")
            try:
                system_prompt = get_default_prompt(db_type)
                logger.warning(f"System prompt was None, using default for {db_type}")
            except ValueError:
                state["query"] = None
                state["error"] = f"Unknown database type: {db_type}"
                return state

        # Format the prompt with the schema
        prompt = system_prompt.format(schema=schema)

        messages = [
            {"role": "system", "content": prompt},
            *state["history"],
            {"role": "user", "content": state["question"]}
        ]
        logger.info(f"Generating SQL for question: {state['question'][:100]}")
        response = llm.invoke(messages)
        state["query"] = response.content.strip()
        logger.info(f"Generated SQL: {state['query'][:200]}")
    except Exception as e:
        state["query"] = None
        state["error"] = str(e)
        logger.error(f"Generation agent error: {str(e)}", exc_info=True)

    return state
