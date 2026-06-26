"""MongoDB query generation agent."""
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
    error = state.get('error') or ''
    logger.info(f"[GENERATION] Retry count: {state.get('retry_count')}, Valid: {state.get('valid')}, Error: {str(error)[:100]}")

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

        logger.info(f"[GENERATION] Generating for question: {state['question'][:100]}")
        response = llm.invoke(messages)
        query_text = response.content.strip()
        logger.info(f"[GENERATION] LLM response: {query_text[:300]}")

        # Detect query type from the generated query
        if query_text.startswith("db."):
            query_type = "shell"
        elif query_text.startswith("["):
            query_type = "aggregation"
        elif query_text.startswith("{"):
            query_type = "find"
        else:
            query_type = None

        state["query"] = query_text
        state["query_type"] = query_type
        state["error"] = None
        logger.info(f"[GENERATION] Detected query type: {query_type}")

    except Exception as e:
        state["query"] = None
        state["error"] = str(e)
        logger.error(f"MongoDB generation agent error: {str(e)}", exc_info=True)

    return state
