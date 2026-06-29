from sqlalchemy import text

def execution_agent(state: dict) -> dict:
    connection = state.get("connection")
    if not connection:
        state["result"] = None
        state["error"] = "Database connection not provided"
        return state

    try:
        with connection.connect() as conn:
            result = conn.execute(text(state["query"]))
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
            state["result"] = {"columns": columns, "rows": rows}
        state["error"] = None
    except Exception as e:
        state["result"] = None
        state["error"] = str(e)
    return state
