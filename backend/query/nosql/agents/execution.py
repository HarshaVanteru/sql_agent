"""MongoDB query execution agent."""
import json
import logging
from bson import ObjectId

logger = logging.getLogger(__name__)


def _convert_objectid_to_str(obj):
    """Recursively convert ObjectId to string for JSON serialization."""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: _convert_objectid_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_objectid_to_str(item) for item in obj]
    return obj


def execution_agent(state: dict) -> dict:
    """Execute MongoDB query and fetch results."""
    connection = state.get("connection")
    database_name = state.get("database_name")
    query = state.get("query")
    query_type = state.get("query_type")

    logger.info(f"[EXECUTION] Connection: {type(connection).__name__ if connection else 'None'}, DB: {database_name}, Query: {query[:100] if query else 'None'}, Type: {query_type}")

    if not connection or not database_name:
        state["result"] = None
        error_msg = f"Missing: connection={bool(connection)}, database_name={bool(database_name)}"
        state["error"] = f"Missing MongoDB connection or database name - {error_msg}"
        logger.error(f"[EXECUTION] {state['error']}")
        return state

    # Handle metadata queries (listCollections, stats, etc)
    if query and "listCollections" in query:
        try:
            db = connection[database_name]
            collections = db.list_collection_names()
            state["result"] = {
                "columns": ["collection_name"],
                "rows": [{"collection_name": name} for name in collections],
                "row_count": len(collections),
            }
            state["error"] = None
            logger.info(f"[EXECUTION] Listed {len(collections)} collections")
            return state
        except Exception as e:
            state["result"] = None
            state["error"] = str(e)
            logger.error(f"[EXECUTION] Metadata query error: {str(e)}", exc_info=True)
            return state

    if not query:
        state["result"] = None
        state["error"] = "No MongoDB query generated"
        logger.error(f"[EXECUTION] {state['error']}")
        return state

    try:
        db = connection[database_name]

        # Detect query type if not set (for backwards compatibility)
        if not query_type:
            if query.startswith("db."):
                query_type = "shell"
            elif query.startswith("["):
                query_type = "aggregation"
            elif query.startswith("{"):
                query_type = "find"

        # Try to infer collection name from query
        # For queries like "db.users.find(...)" extract "users"
        collection_name = None
        if query and "db." in query:
            # Extract collection name from db.collection.method() syntax
            try:
                parts = query.split(".")
                if len(parts) >= 2 and parts[0] == "db":
                    collection_name = parts[1]
            except:
                pass

        if not collection_name:
            state["result"] = None
            state["error"] = "Cannot determine collection name from query"
            logger.error(f"[EXECUTION] {state['error']}")
            return state

        collection = db[collection_name]

        if query_type == "shell":
            # Parse MongoDB shell syntax like db.users.find({...})
            try:
                # Extract method and arguments from shell syntax
                # Pattern: db.collection.method(arg1, arg2, ...)
                import re
                match = re.match(r'db\.(\w+)\.(\w+)\((.*)\)', query)
                if not match:
                    state["result"] = None
                    state["error"] = f"Invalid MongoDB shell syntax: {query[:100]}"
                    logger.error(f"[EXECUTION] {state['error']}")
                    return state

                method = match.group(2)
                args_str = match.group(3)

                if method == "find":
                    parsed_query = json.loads(args_str) if args_str else {}
                    logger.info(f"Executing MongoDB find on collection '{collection_name}': {str(parsed_query)[:200]}")
                    cursor = collection.find(parsed_query).limit(100)
                    rows = list(cursor)

                elif method == "countDocuments":
                    parsed_query = json.loads(args_str) if args_str else {}
                    logger.info(f"Executing countDocuments on collection '{collection_name}'")
                    count = collection.count_documents(parsed_query)
                    rows = [{"count": count}]

                elif method == "listCollections":
                    # Already handled in metadata queries section
                    state["result"] = None
                    state["error"] = "listCollections should be handled as metadata query"
                    return state

                else:
                    state["result"] = None
                    state["error"] = f"Unsupported MongoDB method: {method}"
                    return state

            except json.JSONDecodeError as e:
                state["result"] = None
                state["error"] = f"Invalid JSON in query: {str(e)}"
                logger.error(f"[EXECUTION] {state['error']}")
                return state

        elif query_type == "find":
            # Execute find query (legacy JSON filter format)
            parsed_query = json.loads(query)
            logger.info(f"Executing MongoDB find on collection '{collection_name}': {str(parsed_query)[:200]}")

            cursor = collection.find(parsed_query).limit(100)
            rows = list(cursor)

        elif query_type == "aggregation":
            # Execute aggregation pipeline
            parsed_query = json.loads(query)
            logger.info(f"Executing MongoDB aggregation on collection '{collection_name}': {str(parsed_query)[:200]}")

            cursor = collection.aggregate(parsed_query)
            rows = list(cursor)

        else:
            state["result"] = None
            state["error"] = f"Unknown query type: {query_type}"
            return state

        # Convert ObjectId and other non-JSON types
        rows = [_convert_objectid_to_str(row) for row in rows]

        # Get column names from first row
        columns = list(rows[0].keys()) if rows else []

        logger.info(f"MongoDB query executed successfully - returned {len(rows)} rows")
        state["result"] = {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
        }
        state["error"] = None

    except Exception as e:
        state["result"] = None
        state["error"] = str(e)
        logger.error(f"MongoDB execution error: {str(e)}", exc_info=True)

    return state
