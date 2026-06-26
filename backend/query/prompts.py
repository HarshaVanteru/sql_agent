"""Unified prompts module - imports from SQL and NoSQL specific prompts."""
from backend.query.sql.prompts import get_sql_prompt
from backend.query.nosql.prompts import get_mongodb_prompt


def get_default_prompt(db_type: str) -> str:
    """Get the default prompt for a database type.

    Args:
        db_type: The database type (mysql, postgresql, mongodb)

    Returns:
        The default system prompt for that database type

    Raises:
        ValueError: If the database type is not supported
    """
    db_type = db_type.lower()

    if db_type in ("mysql", "postgresql"):
        return get_sql_prompt(db_type)
    elif db_type == "mongodb":
        return get_mongodb_prompt()
    else:
        raise ValueError(f"Unknown database type: {db_type}")
