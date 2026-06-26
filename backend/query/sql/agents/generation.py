import logging
from langchain_groq import ChatGroq
from sqlalchemy import text
from dotenv import load_dotenv
from backend.query.prompts import get_default_prompt

load_dotenv()

logger = logging.getLogger(__name__)
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)

def _get_schema_from_engine(engine, database_name: str = None):
    """Fetch database schema from an engine."""
    try:
        with engine.connect() as conn:
            # Get database name if not provided
            if not database_name:
                db_result = conn.execute(text("SELECT DATABASE()"))
                database_name = db_result.scalar() or "unknown"

            cols_result = conn.execute(text("""
                SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, DATA_TYPE
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                ORDER BY TABLE_NAME, ORDINAL_POSITION
            """))

            schema = {}
            for table, column, col_type, data_type in cols_result:
                if table not in schema:
                    schema[table] = []
                display_type = col_type if data_type == "enum" else data_type
                schema[table].append(f"{column} ({display_type})")

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

            schema_str = f"Database: {database_name}\n\n"
            schema_str += "\n".join(
                f"Table: {table}\n" + "\n".join(f"  - {c}" for c in cols)
                for table, cols in sorted(schema.items())
            )

            if fks:
                schema_str += "\n\nForeign Keys:\n" + "\n".join(fks)

            return schema_str
    except Exception as e:
        raise

def generation_agent(state: dict) -> dict:
    engine = state.get("engine")
    if not engine:
        state["sql"] = None
        state["error"] = "Database engine not provided"
        return state

    try:
        database_name = state.get("database_name")
        schema = _get_schema_from_engine(engine, database_name)

        # Get system prompt from state (stored in database)
        system_prompt = state.get("system_prompt")

        # If system_prompt is None (old databases), use default based on db_type
        if not system_prompt:
            db_type = state.get("db_type", "mysql")
            try:
                system_prompt = get_default_prompt(db_type)
                logger.warning(f"System prompt was None, using default for {db_type}")
            except ValueError:
                state["sql"] = None
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
        state["sql"] = response.content.strip()
        logger.info(f"Generated SQL: {state['sql'][:200]}")
    except Exception as e:
        state["sql"] = None
        state["error"] = str(e)
        logger.error(f"Generation agent error: {str(e)}", exc_info=True)

    return state
