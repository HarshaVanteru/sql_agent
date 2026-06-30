"""MongoDB query execution agent."""
import logging
from bson import ObjectId
from typing import Any

logger = logging.getLogger(__name__)


def _convert_objectid_to_str(obj: Any) -> Any:
    """Recursively convert ObjectId and other BSON types to JSON-serializable types."""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: _convert_objectid_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_objectid_to_str(item) for item in obj]
    return obj


def _execute_find(collection, query_model) -> list:
    """Execute find query and return results."""
    cursor = collection.find(query_model.filter)

    if query_model.projection:
        cursor = cursor.project(query_model.projection)

    if query_model.sort:
        cursor = cursor.sort([(k, v) for k, v in query_model.sort.items()])

    if query_model.skip:
        cursor = cursor.skip(query_model.skip)

    if query_model.limit:
        cursor = cursor.limit(query_model.limit)
    else:
        cursor = cursor.limit(100)

    return list(cursor)


def _execute_find_one(collection, query_model) -> list:
    """Execute findOne query and return single result."""
    cursor = collection.find(query_model.filter)

    if query_model.projection:
        cursor = cursor.project(query_model.projection)

    if query_model.sort:
        cursor = cursor.sort([(k, v) for k, v in query_model.sort.items()])

    result = cursor.limit(1)
    rows = list(result)
    return rows


def _execute_aggregate(collection, query_model) -> list:
    """Execute aggregation pipeline and return results."""
    cursor = collection.aggregate(query_model.pipeline)
    return list(cursor)


def _execute_count_documents(collection, query_model) -> list:
    """Execute countDocuments and return count."""
    count = collection.count_documents(query_model.filter)
    return [{"count": count}]


def _execute_estimated_document_count(collection, query_model) -> list:
    """Execute estimatedDocumentCount and return count."""
    count = collection.estimated_document_count()
    return [{"count": count}]


def _execute_distinct(collection, query_model) -> list:
    """Execute distinct and return unique values."""
    distinct_values = collection.distinct(query_model.field, query_model.filter)
    return [{"value": val} for val in distinct_values]


def execution_agent(state: dict) -> dict:
    """Execute structured MongoDB query using PyMongo."""
    query_model = state.get("query_model")
    connection = state.get("connection")
    database_name = state.get("database_name")

    logger.info(
        f"[EXECUTION] Model type: {query_model.__class__.__name__ if query_model else 'None'}, "
        f"DB: {database_name}"
    )

    if not connection or not database_name:
        state["result"] = None
        error_msg = f"Missing: connection={bool(connection)}, database_name={bool(database_name)}"
        state["error"] = f"Missing MongoDB connection or database name - {error_msg}"
        logger.error(f"[EXECUTION] {state['error']}")
        return state

    if not query_model:
        state["result"] = None
        state["error"] = "No valid query model to execute"
        logger.error(f"[EXECUTION] {state['error']}")
        return state

    try:
        db = connection[database_name]
        collection = db[query_model.collection]

        # Execute query based on operation type
        if query_model.operation == "find":
            logger.info(
                f"[EXECUTION] Executing find on '{query_model.collection}': {str(query_model.filter)[:200]}"
            )
            rows = _execute_find(collection, query_model)

        elif query_model.operation == "findOne":
            logger.info(
                f"[EXECUTION] Executing findOne on '{query_model.collection}': {str(query_model.filter)[:200]}"
            )
            rows = _execute_find_one(collection, query_model)

        elif query_model.operation == "aggregate":
            logger.info(
                f"[EXECUTION] Executing aggregate on '{query_model.collection}': {len(query_model.pipeline)} stages"
            )
            rows = _execute_aggregate(collection, query_model)

        elif query_model.operation == "countDocuments":
            logger.info(f"[EXECUTION] Executing countDocuments on '{query_model.collection}'")
            rows = _execute_count_documents(collection, query_model)

        elif query_model.operation == "estimatedDocumentCount":
            logger.info(f"[EXECUTION] Executing estimatedDocumentCount on '{query_model.collection}'")
            rows = _execute_estimated_document_count(collection, query_model)

        elif query_model.operation == "distinct":
            logger.info(
                f"[EXECUTION] Executing distinct on '{query_model.collection}', field: '{query_model.field}'"
            )
            rows = _execute_distinct(collection, query_model)

        else:
            state["result"] = None
            state["error"] = f"Unsupported operation: {query_model.operation}"
            logger.error(f"[EXECUTION] {state['error']}")
            return state

        # Convert BSON types to JSON-serializable format
        rows = [_convert_objectid_to_str(row) for row in rows]

        # Extract column names from first row
        columns = list(rows[0].keys()) if rows else []

        logger.info(f"[EXECUTION] Query executed successfully - returned {len(rows)} rows")
        state["result"] = {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
        }
        state["error"] = None

    except Exception as e:
        state["result"] = None
        state["error"] = str(e)
        logger.error(f"[EXECUTION] MongoDB execution error: {str(e)}", exc_info=True)

    return state
