"""MongoDB result formatting agent."""
import logging
import json
from backend.query.nosql.agents.query_formatter_util import query_model_to_mongodb_shell

logger = logging.getLogger(__name__)


def formatting_agent(state: dict) -> dict:
    """Format MongoDB query results into natural language response."""
    result = state.get("result")
    error = state.get("error")
    query_model = state.get("query_model")
    query_json = state.get("query")
    valid = state.get("valid")

    # Store LLM's raw generated response
    llm_response = query_json  # Raw JSON from LLM

    # Parse JSON to structured format
    query_info = None
    if query_json:
        try:
            query_info = json.loads(query_json) if isinstance(query_json, str) else query_json
        except:
            query_info = None

    # Convert model to MongoDB shell syntax for UI display
    mongodb_query = None
    if query_model:
        mongodb_query = query_model_to_mongodb_shell(query_model)
        logger.info(f"[FORMATTING] MongoDB Query: {mongodb_query}")

    # If error occurred, return error response with query info
    if error:
        state["response"] = {
            "status": "error",
            "message": f"Error executing query: {error}",
            "valid": valid,
            "retry_count": state.get("retry_count", 0),
            "llm_response": llm_response,
            "query": mongodb_query,
            "query_json": query_info,
        }
        logger.error(f"[FORMATTING] Error in state: {error}")
        return state

    # If no results found
    if not result or not result.get("rows"):
        state["response"] = {
            "status": "success",
            "message": "No results found.",
            "valid": valid,
            "llm_response": llm_response,
            "query": mongodb_query,
            "query_json": query_info,
            "data": result,
        }
        return state

    rows = result.get("rows", [])
    row_count = result.get("row_count", len(rows))
    columns = result.get("columns", [])

    # For count queries, extract the count value
    if columns == ["count"] and rows:
        count_val = rows[0].get("count", 0)
        state["response"] = {
            "status": "success",
            "message": f"Found {count_val} document(s).",
            "valid": valid,
            "llm_response": llm_response,
            "query": mongodb_query,
            "query_json": query_info,
            "data": result,
        }
        logger.info(f"[FORMATTING] Count query result: {count_val}")
        return state

    # For distinct queries, show unique values
    if columns == ["value"] and rows:
        values = [row.get("value") for row in rows]
        state["response"] = {
            "status": "success",
            "message": f"Found {len(values)} unique value(s).",
            "valid": valid,
            "llm_response": llm_response,
            "query": mongodb_query,
            "query_json": query_info,
            "data": result,
        }
        logger.info(f"[FORMATTING] Distinct query result: {len(values)} values")
        return state

    # For regular find/aggregate queries, include result data
    state["response"] = {
        "status": "success",
        "message": f"Retrieved {row_count} document(s).",
        "valid": valid,
        "llm_response": llm_response,
        "query": mongodb_query,
        "query_json": query_info,
        "data": result,
    }
    logger.info(f"[FORMATTING] Query returned {row_count} rows with columns: {columns}")

    return state
