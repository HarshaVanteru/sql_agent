"""MongoDB query generation agent."""
import json
import logging
from langchain_groq import ChatGroq
from backend.query.nosql.prompts import get_mongodb_prompt
from backend.query.nosql.agents.models import parse_query_json
from backend.query.nosql.agents.query_formatter_util import query_model_to_mongodb_shell

logger = logging.getLogger(__name__)
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)


def _get_mongodb_schema(client, database_name: str) -> str:
    """Fetch schema from MongoDB database."""
    try:
        db = client[database_name]
        collections = db.list_collection_names()

        schema_str = "MongoDB Collections and Sample Fields:\n\n"
        for collection_name in collections:
            collection = db[collection_name]
            sample_doc = collection.find_one()
            if sample_doc:
                fields = list(sample_doc.keys())
                schema_str += f"Collection: {collection_name}\n"
                schema_str += "  Fields:\n"
                for field in fields:
                    value = sample_doc[field]
                    field_type = type(value).__name__
                    schema_str += f"    - {field} ({field_type})\n"
                schema_str += "\n"

        return schema_str if schema_str else "No collections found"
    except Exception as e:
        logger.error(f"Failed to fetch MongoDB schema: {str(e)}", exc_info=True)
        raise


def _extract_json_from_response(response_text: str) -> str:
    """Extract JSON from LLM response, handling markdown code blocks."""
    text = response_text.strip()

    # Remove markdown code blocks if present
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        text = text[start:end].strip()
    elif "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        text = text[start:end].strip()

    return text


def _set_error_state(state: dict, error: str) -> None:
    """Set error state with None values for query fields."""
    state["query"] = None
    state["query_json"] = None
    state["query_model"] = None
    state["error"] = error


def generation_agent(state: dict) -> dict:
    """Generate structured MongoDB query from natural language question."""
    error = state.get("error") or ""
    logger.info(
        f"[GENERATION] Retry count: {state.get('retry_count')}, Valid: {state.get('valid')}, Error: {str(error)[:100]}"
    )

    connection = state.get("connection")
    database_name = state.get("database_name")

    if not connection:
        _set_error_state(state, "MongoDB connection not provided")
        return state

    if not database_name:
        _set_error_state(state, "Database name not provided")
        return state

    try:
        schema = _get_mongodb_schema(connection, database_name)

        # Get system prompt from state (stored in database)
        system_prompt = state.get("system_prompt")

        # If system_prompt is None, use default
        if not system_prompt:
            system_prompt = get_mongodb_prompt()
            logger.warning("System prompt was None, using default MongoDB prompt")

        # Inject the schema into the prompt
        prompt = system_prompt.replace("{schema}", schema)

        messages = [
            {"role": "system", "content": prompt},
            *state["history"],
            {"role": "user", "content": state["question"]},
        ]

        logger.info(f"[GENERATION] Generating for question: {state['question'][:100]}")
        response = llm.invoke(messages)
        response_text = response.content.strip()
        logger.info(f"[GENERATION] LLM response: {response_text[:300]}")

        # Extract JSON from response (handle markdown code blocks)
        query_json = _extract_json_from_response(response_text)

        # Check for unsupported query
        if "UNSUPPORTED_QUERY" in query_json:
            _set_error_state(state, "Query is not supported by the system")
            logger.info("[GENERATION] Query marked as unsupported by LLM")
            return state

        # Validate JSON structure and parse into model
        try:
            query_model = parse_query_json(query_json)
            logger.info(
                f"[GENERATION] Valid {query_model.operation} query for collection '{query_model.collection}'"
            )
        except (json.JSONDecodeError, ValueError) as e:
            _set_error_state(state, f"Invalid query structure: {str(e)}")
            logger.warning(f"[GENERATION] Failed to parse query: {str(e)}")
            return state

        # Convert model to MongoDB shell query for user display
        shell_query = query_model_to_mongodb_shell(query_model)

        # Store shell query for UI, raw JSON for formatting, model for validation/execution
        state["query"] = shell_query
        state["query_json"] = query_json
        state["query_model"] = query_model
        state["error"] = None

    except Exception as e:
        _set_error_state(state, str(e))
        logger.error(f"MongoDB generation agent error: {str(e)}", exc_info=True)

    return state
