from sqlalchemy import text

def validation_agent(state: dict) -> dict:
    query = state.get("query")

    if not query:
        state["valid"] = False
        state["error"] = state.get("error", "No SQL query generated")
        return state

    query_lower = query.strip().lower()
    state["retry_count"] = state.get("retry_count", 0) + 1

    if not query_lower.startswith("select"):
        state["valid"] = False
        state["error"] = "Only SELECT statements are allowed."
        return state

    connection = state.get("connection")
    if not connection:
        state["valid"] = False
        state["error"] = "Database connection not provided"
        return state

    try:
        with connection.connect() as conn:
            conn.execute(text(f"EXPLAIN {state['query']}"))
        state["valid"] = True
        state["error"] = None
    except Exception as e:
        state["valid"] = False
        state["error"] = str(e)

    return state
