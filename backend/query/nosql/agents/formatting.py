"""MongoDB result formatting agent."""
import logging
import json

logger = logging.getLogger(__name__)


def _parse_query_json(query_json: str) -> dict | None:
    """Parse raw query JSON to structured format."""
    if not query_json:
        return None
    try:
        return json.loads(query_json) if isinstance(query_json, str) else query_json
    except (json.JSONDecodeError, TypeError):
        return None


def _build_response(status: str, message: str, state: dict, query_info: dict | None) -> dict:
    """Build response dictionary with common fields."""
    return {
        "status": status,
        "message": message,
        "valid": state.get("valid"),
        "llm_response": state.get("query_json"),
        "query": state.get("query"),
        "query_json": query_info,
        "data": state.get("result"),
        **({"retry_count": state.get("retry_count")} if status == "error" else {}),
    }


def formatting_agent(state: dict) -> dict:
    """Format MongoDB query results into natural language response."""
    error = state.get("error")
    result = state.get("result")
    query_info = _parse_query_json(state.get("query_json"))

    # Handle errors
    if error:
        state["response"] = _build_response("error", f"Error executing query: {error}", state, query_info)
        logger.error(f"[FORMATTING] Error: {error}")
        return state

    # Handle no results
    if not result or not result.get("rows"):
        state["response"] = _build_response("success", "No results found.", state, query_info)
        return state

    rows = result.get("rows", [])
    columns = result.get("columns", [])
    row_count = len(rows)

    # Format message based on query type
    if columns == ["count"] and rows:
        message = f"Found {rows[0].get('count', 0)} document(s)."
        logger.info(f"[FORMATTING] Count query result: {rows[0].get('count', 0)}")
    elif columns == ["value"] and rows:
        message = f"Found {row_count} unique value(s)."
        logger.info(f"[FORMATTING] Distinct query result: {row_count} values")
    else:
        message = f"Retrieved {row_count} document(s)."
        logger.info(f"[FORMATTING] Query returned {row_count} rows with columns: {columns}")

    state["response"] = _build_response("success", message, state, query_info)
    return state
