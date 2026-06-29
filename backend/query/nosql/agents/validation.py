"""MongoDB query validation agent."""
import json
import logging

logger = logging.getLogger(__name__)


def _explain_query(client, database_name: str, collection_name: str, query_type: str, query_filter: dict):
    """Validate query using explain() to check execution plan."""
    try:
        db = client[database_name]
        collection = db[collection_name]

        if query_type == "find":
            # Use explain() to validate find query
            explain_result = collection.find(query_filter).explain()
            execution_stats = explain_result.get("executionStats", {})
            execution_stage = execution_stats.get("executionStages", {})

            # Check if full collection scan (inefficient)
            if execution_stage.get("stage") == "COLLSCAN":
                logger.warning(f"[EXPLAIN] Full collection scan detected for query: {str(query_filter)[:100]}")
                return True, "Warning: Full collection scan (may be slow)"

            docs_examined = execution_stats.get("totalDocsExamined", 0)
            docs_returned = execution_stats.get("nReturned", 0)

            logger.info(f"[EXPLAIN] Find query: examined {docs_examined} docs, returned {docs_returned}")
            return True, None

        elif query_type == "aggregation":
            # Use explain() to validate aggregation pipeline
            explain_result = collection.aggregate(query_filter, explain=True)
            logger.info(f"[EXPLAIN] Aggregation pipeline validated")
            return True, None

        return True, None

    except Exception as e:
        logger.error(f"[EXPLAIN] Query validation failed: {str(e)}")
        return False, str(e)


def validation_agent(state: dict) -> dict:
    """Validate MongoDB query syntax, structure, and execution plan."""
    logger.info(f"[VALIDATION] Query: {state.get('query', '')[:100] if state.get('query') else 'None'}, Type: {state.get('query_type')}, Retry: {state.get('retry_count')}")

    query = state.get("query")
    query_type = state.get("query_type")
    connection = state.get("connection")
    database_name = state.get("database_name")

    if not query:
        state["valid"] = False
        state["error"] = state.get("error", "No MongoDB query generated")
        return state

    state["retry_count"] = state.get("retry_count", 0) + 1

    # Metadata queries and shell syntax skip JSON validation
    if "listCollections" in query or "stats()" in query or query_type == "shell" or (query and query.startswith("db.")):
        state["valid"] = True
        state["error"] = None
        if query_type is None and query.startswith("db."):
            state["query_type"] = "shell"
        logger.info(f"[VALIDATION] Metadata/Shell query accepted: {query[:100]}")
        return state

    try:
        # Validate JSON structure and syntax
        if query_type == "aggregation":
            # Should be an array of stages
            parsed = json.loads(query)
            if not isinstance(parsed, list):
                state["valid"] = False
                state["error"] = "Aggregation pipeline must be a JSON array"
                return state

            # Validate each stage
            allowed_stages = {
                "$match", "$group", "$sort", "$limit", "$skip", "$project",
                "$count", "$lookup", "$unwind", "$bucket", "$bucketAuto",
                "$facet", "$out", "$merge", "$addFields", "$replaceRoot",
                "$redact", "$geoNear", "$sample", "$indexStats"
            }

            for stage in parsed:
                if not isinstance(stage, dict):
                    state["valid"] = False
                    state["error"] = f"Each pipeline stage must be an object"
                    return state

                stage_keys = set(stage.keys())
                invalid_stages = stage_keys - allowed_stages
                if invalid_stages:
                    state["valid"] = False
                    state["error"] = f"Unknown pipeline stages: {invalid_stages}"
                    return state

        elif query_type == "find":
            # Should be a valid filter object
            parsed = json.loads(query)
            if not isinstance(parsed, dict):
                state["valid"] = False
                state["error"] = "Find filter must be a JSON object"
                return state

            # Validate operators
            valid_operators = {
                "$eq", "$gt", "$lt", "$gte", "$lte", "$ne", "$in", "$nin",
                "$and", "$or", "$not", "$exists", "$type", "$regex", "$text",
                "$where", "$mod", "$all", "$elemMatch", "$size", "$bitsAllSet",
                "$bitsAnySet", "$bitsAllClear", "$bitsClear"
            }

            def validate_operators(obj):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if key.startswith("$"):
                            if key not in valid_operators:
                                return False, f"Unknown operator: {key}"
                        if isinstance(value, dict):
                            valid, msg = validate_operators(value)
                            if not valid:
                                return False, msg
                return True, None

            valid, error_msg = validate_operators(parsed)
            if not valid:
                state["valid"] = False
                state["error"] = error_msg
                return state

        # Run explain() to validate execution plan
        if connection and database_name and query_type in ("find", "aggregation"):
            # Extract collection name from query if available
            collection_name = state.get("collection_name")
            if not collection_name and query.startswith("db."):
                # Try to extract from shell syntax
                try:
                    parts = query.split(".")
                    if len(parts) >= 2:
                        collection_name = parts[1]
                except:
                    pass

            if collection_name:
                valid, warning = _explain_query(connection, database_name, collection_name, query_type, parsed)
                if not valid:
                    state["valid"] = False
                    state["error"] = warning
                    return state
                if warning:
                    logger.warning(f"[VALIDATION] {warning}")

        state["valid"] = True
        state["error"] = None
        logger.info(f"MongoDB {query_type} query validated successfully")

    except json.JSONDecodeError as e:
        state["valid"] = False
        state["error"] = f"Invalid JSON: {str(e)}"
        logger.error(f"JSON validation error: {str(e)}")

    except Exception as e:
        state["valid"] = False
        state["error"] = str(e)
        logger.error(f"MongoDB validation agent error: {str(e)}", exc_info=True)

    return state
