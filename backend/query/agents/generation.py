import logging
from langchain_groq import ChatGroq
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)

def _get_schema_from_engine(engine):
    """Fetch database schema from an engine."""
    try:
        with engine.connect() as conn:
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

            schema_str = "\n".join(
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
        schema = _get_schema_from_engine(engine)

        prompt = f"""You are a MySQL query generator for an e-commerce analytics system.

Your job is to convert natural language questions into valid MySQL SELECT queries.

Rules:
- Return only the raw SQL query, nothing else. No explanation, no markdown, no backticks.
- Only generate SELECT statements. Never INSERT, UPDATE, DELETE, or DROP.
- Always use table aliases for readability when joining tables.
- Always add a LIMIT 100 unless the user explicitly asks for more or asks for aggregated results.
- Use exact column and table names from the schema below.
- If the question is ambiguous, make the most reasonable assumption and generate the query.
- Always use SELECT DISTINCT when the query involves a JOIN that could produce duplicate rows.
- Never use SELECT * — select only columns meaningful to the user, excluding raw foreign key IDs unless specifically asked.

Database schema:
{schema}
"""

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
