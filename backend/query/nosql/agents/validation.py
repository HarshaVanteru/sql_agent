"""MongoDB query validation agent."""
import logging
from typing import Set, Tuple

logger = logging.getLogger(__name__)

# Allowed MongoDB filter operators
FILTER_OPERATORS: Set[str] = {
    "$eq",
    "$gt",
    "$lt",
    "$gte",
    "$lte",
    "$ne",
    "$in",
    "$nin",
    "$and",
    "$or",
    "$not",
    "$exists",
    "$type",
    "$regex",
    "$text",
    "$where",
    "$mod",
    "$all",
    "$elemMatch",
    "$size",
    "$bitsAllSet",
    "$bitsAnySet",
    "$bitsAllClear",
    "$bitsClear",
}

# Allowed MongoDB aggregation pipeline stages
PIPELINE_STAGES: Set[str] = {
    "$match",
    "$group",
    "$sort",
    "$limit",
    "$skip",
    "$project",
    "$count",
    "$lookup",
    "$unwind",
    "$bucket",
    "$bucketAuto",
    "$facet",
    "$out",
    "$merge",
    "$addFields",
    "$replaceRoot",
    "$redact",
    "$geoNear",
    "$sample",
    "$indexStats",
}


def _validate_filter_operators(obj: dict) -> Tuple[bool, str | None]:
    """
    Recursively validate all operators in a filter object.

    Args:
        obj: Filter dictionary to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(obj, dict):
        return True, None

    for key, value in obj.items():
        if key.startswith("$"):
            if key not in FILTER_OPERATORS:
                return False, f"Unknown filter operator: {key}"
        if isinstance(value, dict):
            valid, error = _validate_filter_operators(value)
            if not valid:
                return False, error

    return True, None


def _validate_pipeline_stages(pipeline: list) -> Tuple[bool, str | None]:
    """
    Validate all stages in an aggregation pipeline.

    Args:
        pipeline: List of pipeline stage dictionaries

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(pipeline, list):
        return False, "Pipeline must be a list"

    if not pipeline:
        return False, "Pipeline cannot be empty"

    for idx, stage in enumerate(pipeline):
        if not isinstance(stage, dict):
            return False, f"Stage {idx} must be a dict, got {type(stage).__name__}"

        if not stage:
            return False, f"Stage {idx} cannot be empty"

        # Check that stage has valid operators
        stage_keys = set(stage.keys())
        invalid_keys = stage_keys - PIPELINE_STAGES
        if invalid_keys:
            return False, f"Stage {idx} contains unknown operators: {invalid_keys}"

    return True, None


def _collection_exists(client, database_name: str, collection_name: str) -> bool:
    """Check if collection exists in database."""
    try:
        db = client[database_name]
        return collection_name in db.list_collection_names()
    except Exception as e:
        logger.warning(f"Could not verify collection existence: {str(e)}")
        # Don't fail validation if we can't check - connection might be read-only
        return True


def validation_agent(state: dict) -> dict:
    """Validate structured MongoDB query models."""
    query_model = state.get("query_model")
    connection = state.get("connection")
    database_name = state.get("database_name")

    # Increment retry count FIRST, before any early returns
    state["retry_count"] = state.get("retry_count", 0) + 1

    logger.info(
        f"[VALIDATION] Model type: {query_model.__class__.__name__ if query_model else 'None'}, "
        f"Retry: {state.get('retry_count')}"
    )

    if not query_model:
        state["valid"] = False
        state["error"] = state.get("error", "No valid query model generated")
        return state

    try:
        # Validate collection exists
        if connection and database_name:
            if not _collection_exists(connection, database_name, query_model.collection):
                state["valid"] = False
                state["error"] = f"Collection '{query_model.collection}' not found"
                logger.warning(f"[VALIDATION] {state['error']}")
                return state

        # Operation-specific validation
        if query_model.operation in ("find", "findOne", "countDocuments"):
            # Validate filter operators
            valid, error = _validate_filter_operators(query_model.filter)
            if not valid:
                state["valid"] = False
                state["error"] = error
                logger.error(f"[VALIDATION] {error}")
                return state

        elif query_model.operation == "aggregate":
            # Validate pipeline stages
            valid, error = _validate_pipeline_stages(query_model.pipeline)
            if not valid:
                state["valid"] = False
                state["error"] = error
                logger.error(f"[VALIDATION] {error}")
                return state

        elif query_model.operation == "distinct":
            # Validate filter operators
            valid, error = _validate_filter_operators(query_model.filter)
            if not valid:
                state["valid"] = False
                state["error"] = error
                return state

        state["valid"] = True
        state["error"] = None
        logger.info(f"[VALIDATION] {query_model.operation} query validated successfully")

    except Exception as e:
        state["valid"] = False
        state["error"] = str(e)
        logger.error(f"MongoDB validation agent error: {str(e)}", exc_info=True)

    return state
