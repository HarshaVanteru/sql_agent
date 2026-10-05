"""Connections and query execution for the databases users connect.

MySQL and PostgreSQL differ only in their driver, the name shown to a user, and
the wording their drivers use for failures. Everything else -- building the URL,
pooling, running a query, shaping the result -- is identical, so it lives here
once and `_DIALECTS` holds the differences.
"""
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import quote_plus

import logfire
from fastapi import HTTPException, status
from sqlalchemy import text

from app.core.config import settings
from app.query.databases.engines import get_engine


@dataclass(frozen=True)
class _Dialect:
    label: str  # what a user should see: "MySQL", not "mysql+pymysql"
    driver: str
    # Passed to the driver. Every entry is a deadline: these are databases we
    # do not run, reached over a network we do not control, and a request with
    # no ceiling on it holds a threadpool worker until the far end decides it
    # is finished.
    connect_args: dict


_DIALECTS: dict[str, _Dialect] = {
    "mysql": _Dialect(
        label="MySQL",
        driver="mysql+pymysql",
        connect_args={
            "connect_timeout": settings.DB_CONNECT_TIMEOUT,
            # MySQL has no per-session statement timeout we can set here, so
            # the read deadline is what bounds a long query.
            "read_timeout": settings.DB_STATEMENT_TIMEOUT,
            "write_timeout": settings.DB_STATEMENT_TIMEOUT,
        },
    ),
    "postgresql": _Dialect(
        label="PostgreSQL",
        driver="postgresql+psycopg2",
        connect_args={
            "connect_timeout": settings.DB_CONNECT_TIMEOUT,
            # Postgres will cancel the query itself at this point, which is
            # better than us walking away and leaving it running.
            "options": f"-c statement_timeout={settings.DB_STATEMENT_TIMEOUT * 1000}",
        },
    ),
}

SUPPORTED_DB_TYPES = frozenset(_DIALECTS)

# Messages a user can act on, shared by both dialects so they cannot drift apart.
_INVALID_LOGIN = "Invalid username or password"
_NO_DATABASE = "Database does not exist"
_BAD_HOST = "Invalid hostname - cannot resolve address"
_TIMEOUT = "Connection timeout - server not responding"
_CANNOT_CONNECT = "Cannot connect to {label} server at {host}:{port}"

# Ordered: the first rule that matches the driver's (lowercased) error wins.
# The wording is the driver's, so the patterns genuinely differ per dialect --
# only the messages they map onto are shared.
_ERROR_RULES: dict[str, tuple[tuple[Callable[[str], bool], str], ...]] = {
    "mysql": (
        (lambda e: "access denied" in e or "1045" in e, _INVALID_LOGIN),
        (lambda e: "unknown database" in e or "1049" in e, _NO_DATABASE),
        (
            lambda e: "can't connect" in e or "2003" in e or "connection refused" in e,
            _CANNOT_CONNECT,
        ),
        (lambda e: "getaddrinfo failed" in e or "11001" in e, _BAD_HOST),
        (lambda e: "connection timeout" in e, _TIMEOUT),
    ),
    "postgresql": (
        (lambda e: "password authentication failed" in e, _INVALID_LOGIN),
        # Both parts required: `role "bob" does not exist` is an auth failure,
        # not a missing database.
        (lambda e: "database" in e and "does not exist" in e, _NO_DATABASE),
        (lambda e: "could not translate" in e or "unknown host" in e, _BAD_HOST),
        (lambda e: "connection refused" in e, _CANNOT_CONNECT),
        (lambda e: "timeout" in e, _TIMEOUT),
    ),
}


def dialect_label(db_type: str) -> str:
    """The user-facing name of a database type ("mysql" -> "MySQL")."""
    dialect = _DIALECTS.get(db_type.lower())
    return dialect.label if dialect else db_type


def _label_of_engine(engine) -> str:
    """The user-facing name behind an existing engine."""
    return dialect_label(engine.dialect.name)


def connection_error_message(db_type: str, error: Exception, host: str, port: int) -> str:
    """Turn a driver's connection error into something a user can act on.

    `host` and `port` are passed in rather than dug out of the error text: the
    message is what we already know, not what the driver happened to phrase.
    """
    text_ = str(error).lower()
    for matches, message in _ERROR_RULES.get(db_type.lower(), ()):
        if matches(text_):
            return message.format(
                label=dialect_label(db_type), host=host, port=port
            )
    return f"Connection failed: {str(error).split('(')[0].strip()}"


def create_connection(
    db_type: str, host: str, port: int, username: str, password: str, database_name: str
):
    """Create an engine for `db_type`, which must be a supported database type."""
    dialect = _DIALECTS.get(db_type.lower())
    if dialect is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "UNSUPPORTED_DB",
                "message": f"Database type '{db_type}' is not supported",
            },
        )

    try:
        encoded_user = quote_plus(username)
        encoded_password = quote_plus(password)
        db_url = f"{dialect.driver}://{encoded_user}:{encoded_password}@{host}:{port}/{database_name}"
        logfire.debug(
            "{label} connection URL: {driver}://{username}:***@{host}:{port}/{database_name}",
            label=dialect.label,
            driver=dialect.driver,
            username=username,
            host=host,
            port=port,
            database_name=database_name,
        )
        return get_engine(db_url, dialect.connect_args)
    except Exception as e:
        logfire.exception(
            "Failed to create {label} connection: {error}", label=dialect.label, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "CONNECTION_ERROR",
                "message": f"Failed to connect to {dialect.label}: {str(e)}",
            },
        ) from e


def execute_query(engine, query: str) -> dict:
    """Execute a query against a user's database."""
    label = _label_of_engine(engine)
    try:
        with logfire.span(
            "Executing {label} query: {query_preview}...",
            label=label,
            query_preview=query[:100],
        ):
            with engine.connect() as conn:
                query_result = conn.execute(text(query))
                columns = list(query_result.keys())
                rows = [dict(zip(columns, row, strict=True)) for row in query_result.fetchall()]

            logfire.info(
                "{label} query executed successfully - returned {row_count} rows",
                label=label,
                row_count=len(rows),
            )
            return {
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
            }
    except Exception as e:
        logfire.exception(
            "{label} query execution failed: {error}", label=label, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "QUERY_ERROR", "message": f"Query execution failed: {str(e)}"},
        ) from e
