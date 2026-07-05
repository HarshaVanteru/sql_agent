"""Utility to format MongoDB queries into shell syntax for UI display."""
from typing import Any, Dict, List


def _format_value(value: Any) -> str:
    """Format a value for MongoDB shell syntax."""
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, dict):
        return format_dict(value)
    elif isinstance(value, list):
        return format_list(value)
    else:
        return str(value)


def format_dict(obj: Dict[str, Any]) -> str:
    """Format dictionary as MongoDB object."""
    if not obj:
        return "{}"

    items = []
    for key, value in obj.items():
        formatted_value = _format_value(value)
        items.append(f"{key}: {formatted_value}")

    return "{ " + ", ".join(items) + " }"


def format_list(lst: List[Any]) -> str:
    """Format list as MongoDB array."""
    if not lst:
        return "[]"

    items = [_format_value(item) for item in lst]
    return "[ " + ", ".join(items) + " ]"


def query_model_to_mongodb_shell(query_model: Any) -> str:
    """
    Convert Pydantic query model to MongoDB shell syntax.

    Args:
        query_model: FindQuery, AggregateQuery, etc.

    Returns:
        MongoDB shell query string (e.g., "db.users.find({}).limit(100)")
    """
    if not query_model:
        return None

    collection = query_model.collection
    operation = query_model.operation

    # Build base query
    if operation == "find":
        filter_str = format_dict(query_model.filter)
        query = f"db.{collection}.find({filter_str})"

        # Add projection if present
        if hasattr(query_model, 'projection') and query_model.projection:
            projection_str = format_dict(query_model.projection)
            query = f"db.{collection}.find({filter_str}, {projection_str})"

        # Add sort
        if hasattr(query_model, 'sort') and query_model.sort:
            sort_str = format_dict(query_model.sort)
            query += f".sort({sort_str})"

        # Add skip
        if hasattr(query_model, 'skip') and query_model.skip:
            query += f".skip({query_model.skip})"

        # Add limit
        if hasattr(query_model, 'limit') and query_model.limit:
            query += f".limit({query_model.limit})"

        return query

    elif operation == "findOne":
        filter_str = format_dict(query_model.filter)
        query = f"db.{collection}.findOne({filter_str})"

        # Add projection if present
        if hasattr(query_model, 'projection') and query_model.projection:
            projection_str = format_dict(query_model.projection)
            query = f"db.{collection}.findOne({filter_str}, {projection_str})"

        return query

    elif operation == "aggregate":
        pipeline_str = format_list(query_model.pipeline)
        query = f"db.{collection}.aggregate({pipeline_str})"
        return query

    elif operation == "countDocuments":
        filter_str = format_dict(query_model.filter)
        query = f"db.{collection}.countDocuments({filter_str})"
        return query

    elif operation == "estimatedDocumentCount":
        query = f"db.{collection}.estimatedDocumentCount()"
        return query

    elif operation == "distinct":
        filter_str = format_dict(query_model.filter)
        field = query_model.field
        query = f"db.{collection}.distinct(\"{field}\", {filter_str})"
        return query

    else:
        return f"db.{collection}.{operation}()"
