from sqlalchemy import text

def validation_agent(state: dict) -> dict:
    sql = state["sql"].strip().lower()
    state["retry_count"] = state.get("retry_count", 0) + 1

    if not sql.startswith("select"):
        state["valid"] = False
        state["error"] = "Only SELECT statements are allowed."
        return state

    engine = state.get("engine")
    if not engine:
        state["valid"] = False
        state["error"] = "Database engine not provided"
        return state

    try:
        with engine.connect() as conn:
            conn.execute(text(f"EXPLAIN {state['sql']}"))
        state["valid"] = True
        state["error"] = None
    except Exception as e:
        state["valid"] = False
        state["error"] = str(e)

    return state
