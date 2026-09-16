"""Tools the SQL agent can call.

Schema introspection goes through SQLAlchemy's inspector rather than raw
information_schema queries so the same tools work on every supported dialect.
"""
import logfire
from langchain_core.tools import tool
from sqlalchemy import inspect, text

from app.core.config import settings
from app.query.guard import guard_query

# Rows fetched from the database at most, per query.
MAX_ROWS = settings.AGENT_MAX_ROWS

# Rows shown back to the model. The user still gets the full result set; the
# model only needs a sample to judge whether the query answered the question,
# and feeding it thousands of rows would burn the context window.
LLM_ROW_SAMPLE = settings.AGENT_ROW_SAMPLE


class QueryRecorder:
    """Holds the last successful query and its full result.

    The agent may run several queries while exploring; the last one that
    succeeded is what gets returned to the user.
    """

    def __init__(self):
        self.query: str | None = None
        self.columns: list[str] = []
        self.rows: list[dict] = []

    @property
    def has_result(self) -> bool:
        return self.query is not None

    def record(self, query: str, columns: list[str], rows: list[dict]) -> None:
        self.query = query
        self.columns = columns
        self.rows = rows


def _format_rows(columns: list[str], rows: list[dict]) -> str:
    """Render a row sample compactly for the model."""
    if not rows:
        return "0 rows."

    sample = rows[:LLM_ROW_SAMPLE]
    lines = [" | ".join(columns)]
    lines += [" | ".join("NULL" if r[c] is None else str(r[c]) for c in columns) for r in sample]

    footer = f"({len(rows)} rows"
    if len(rows) > len(sample):
        footer += f", showing first {len(sample)}"
    footer += ")"
    lines.append(footer)

    return "\n".join(lines)


# What a tool hands back to the model when something fails. A driver error can
# be forty lines with the whole generated SQL in it, and every one of those
# lines is context the model then cannot use for the actual question.
_MAX_TOOL_ERROR = 300


def _brief(error: Exception) -> str:
    """The first line of an error, capped. Enough to self-correct from."""
    text = " ".join(str(error).split("\n")[0].split())
    return text[:_MAX_TOOL_ERROR] + ("..." if len(text) > _MAX_TOOL_ERROR else "")


# SQLAlchemy's Postgres inspector joins pg_collation to report column
# collations, and a read-only account is often not granted it -- which is how
# describing a table fails outright on a database the agent can otherwise read
# perfectly well. This asks information_schema for the three things actually
# needed instead.
#
# Our SQL, not the model's, so it does not go through the guard: the guard
# exists to stop the model reaching system schemas, and this is the introspection
# the model is supposed to get *instead* of trying that itself.
_COLUMNS_FALLBACK = """
    SELECT table_schema, column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = :table_name
    ORDER BY table_schema, ordinal_position
"""


def _columns_via_information_schema(engine, table_name: str) -> list[str]:
    """Column lines for `table_name`, using only information_schema."""
    with engine.connect() as conn:
        rows = conn.execute(text(_COLUMNS_FALLBACK), {"table_name": table_name}).fetchall()

    lines = []
    for schema, column, data_type, nullable in rows:
        null = "" if nullable == "YES" else " NOT NULL"
        prefix = f"{schema}." if len({r[0] for r in rows}) > 1 else ""
        lines.append(f"  - {prefix}{column} ({data_type}){null}")
    return lines


def build_tools(engine):
    """Build the agent's tools bound to `engine`, plus the recorder they write to."""
    recorder = QueryRecorder()
    # Bound once from the engine so the guard can reject cross-database and
    # system-schema access for this specific connection.
    dialect = engine.dialect.name
    database_name = engine.url.database

    @tool
    def list_tables() -> str:
        """List every table in the database. Use this before guessing table names."""
        try:
            names = inspect(engine).get_table_names()
        except Exception as e:
            logfire.warning("list_tables failed: {error}", error=_brief(e))
            return f"Error listing tables: {_brief(e)}"
        return ", ".join(sorted(names)) if names else "(database has no tables)"

    @tool
    def describe_table(table_name: str) -> str:
        """Show one table's columns, types, and foreign keys. Use before writing a query."""
        try:
            inspector = inspect(engine)
            if table_name not in inspector.get_table_names():
                available = ", ".join(sorted(inspector.get_table_names()))
                return f"No table named '{table_name}'. Available tables: {available}"

            lines = [f"Table: {table_name}"]
            try:
                for col in inspector.get_columns(table_name):
                    null = "" if col.get("nullable", True) else " NOT NULL"
                    lines.append(f"  - {col['name']} ({col['type']}){null}")
            except Exception as e:
                # Usually a privilege the inspector needs and this account does
                # not have. The columns are still readable a simpler way.
                logfire.info(
                    "Inspector could not read {table_name}, using information_schema: {error}",
                    table_name=table_name,
                    error=_brief(e),
                )
                lines.extend(_columns_via_information_schema(engine, table_name))

            if len(lines) == 1:
                return f"No column information available for '{table_name}'."

            try:
                for fk in inspector.get_foreign_keys(table_name):
                    cols = ", ".join(fk["constrained_columns"])
                    ref_cols = ", ".join(fk["referred_columns"])
                    lines.append(f"  FK: {cols} -> {fk['referred_table']}.{ref_cols}")
            except Exception as e:
                # Foreign keys are a nicety; columns are the job.
                logfire.info("Could not read foreign keys: {error}", error=_brief(e))

            return "\n".join(lines)
        except Exception as e:
            logfire.warning(
                "describe_table({table_name}) failed: {error}",
                table_name=table_name,
                error=_brief(e),
            )
            return f"Error describing '{table_name}': {_brief(e)}"

    @tool
    def run_query(query: str) -> str:
        """Run one read-only SELECT and return a sample of the rows.

        The last query that succeeds is what the user sees, so make it complete.
        """
        with logfire.span("Agent query: {query_preview}", query_preview=query[:200]):
            rejection = guard_query(query, dialect=dialect, database_name=database_name)
            if rejection:
                logfire.warning("Agent query rejected: {rejection}", rejection=rejection)
                return f"Rejected: {rejection}"

            try:
                with engine.connect() as conn:
                    result = conn.execute(text(query))
                    columns = list(result.keys())
                    rows = [
                        dict(zip(columns, row, strict=True))
                        for row in result.fetchmany(MAX_ROWS)
                    ]
            except Exception as e:
                # Handed back verbatim so the agent can correct itself from the
                # database's own error rather than guessing.
                logfire.info(
                    "Agent query failed, returning error to agent: {error}", error=str(e)
                )
                return f"Error: {e}"

            recorder.record(query, columns, rows)
            logfire.info(
                "Agent query succeeded ({row_count} rows): {query_preview}",
                row_count=len(rows),
                query_preview=query[:200],
            )
            return _format_rows(columns, rows)

    return [list_tables, describe_table, run_query], recorder
