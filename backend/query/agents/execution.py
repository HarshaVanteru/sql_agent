from sqlalchemy import text

def execution_agent(state: dict) -> dict:
    engine = state.get("engine")
    if not engine:
        state["result"] = None
        state["error"] = "Database engine not provided"
        return state

    try:
        with engine.connect() as conn:
            result = conn.execute(text(state["sql"]))
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
            state["result"] = {"columns": columns, "rows": rows}
        state["error"] = None
    except Exception as e:
        state["result"] = None
        state["error"] = str(e)
    return state
