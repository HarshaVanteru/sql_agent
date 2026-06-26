"""MongoDB query generation agent."""
import json
import logging
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from backend.query.nosql.prompts import get_mongodb_prompt

load_dotenv()

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


def generation_agent(state: dict) -> dict:
    """Generate MongoDB query from natural language question."""
    client = state.get("client")
    database_name = state.get("database_name")

    if not client:
        state["query"] = None
        state["error"] = "MongoDB client not provided"
        return state

    if not database_name:
        state["query"] = None
        state["error"] = "Database name not provided"
        return state

    try:
        schema = _get_mongodb_schema(client, database_name)

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
            {"role": "user", "content": state["question"]}
        ]

        logger.info(f"Generating MongoDB query for question: {state['question'][:100]}")
        response = llm.invoke(messages)
        query_text = response.content.strip()
        logger.info(f"Generated query: {query_text[:200]}")

        # Validate JSON by parsing it
        try:
            # Try to parse as JSON (could be filter or pipeline)
            if query_text.startswith('['):
                json.loads(query_text)  # Aggregation pipeline
                state["query"] = query_text
                state["query_type"] = "aggregation"
            else:
                json.loads(query_text)  # Filter object
                state["query"] = query_text
                state["query_type"] = "find"
        except json.JSONDecodeError as e:
            state["query"] = None
            state["error"] = f"Generated invalid JSON: {str(e)}"
            logger.error(f"Invalid MongoDB query generated: {query_text}")
            return state

        state["error"] = None

    except Exception as e:
        state["query"] = None
        state["error"] = str(e)
        logger.error(f"MongoDB generation agent error: {str(e)}", exc_info=True)

    return state
