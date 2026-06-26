def formatting_agent(state: dict) -> dict:
    result = state.get("result")

    if not result or not result["rows"]:
        state["response"] = "No results found."
        return state

    state["response"] = result
    return state
