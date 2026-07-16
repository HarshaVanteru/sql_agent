"""Read-only guard for LLM-generated SQL.

Shared by the query pipeline and the agent's run_query tool. Any path that lets
a model put SQL in front of a user's database must go through guard_query first.
"""
import re

# A valid query is a single read: a SELECT, or a CTE that resolves to one.
_READ_PREFIX = re.compile(r"^(?:select|with)\b", re.IGNORECASE)

# Postgres allows data-modifying statements inside a CTE, which a bare
# "starts with WITH" check would wave through:
#   WITH x AS (DELETE FROM users RETURNING *) SELECT * FROM x
_CTE_WRITE = re.compile(r"\b(?:insert|update|delete|merge)\b", re.IGNORECASE)


def _sanitize(query: str) -> str:
    """Blank out string literals, quoted identifiers, and comments.

    The guards below inspect keywords and semicolons, and must not be fooled by
    either appearing inside a literal (`SELECT ';' FROM t` is one statement).
    """
    out = []
    i, n = 0, len(query)

    while i < n:
        ch = query[i]

        if ch in ("'", '"', "`"):
            quote = ch
            i += 1
            while i < n:
                # MySQL honours backslash escapes inside single-quoted strings.
                if query[i] == "\\" and quote == "'" and i + 1 < n:
                    i += 2
                    continue
                if query[i] == quote:
                    if i + 1 < n and query[i + 1] == quote:  # '' escapes a quote
                        i += 2
                        continue
                    i += 1
                    break
                i += 1
            out.append(" ")
            continue

        if query.startswith("--", i):
            end = query.find("\n", i)
            i = n if end == -1 else end
            out.append(" ")
            continue

        if query.startswith("/*", i):
            end = query.find("*/", i + 2)
            i = n if end == -1 else end + 2
            out.append(" ")
            continue

        out.append(ch)
        i += 1

    return "".join(out)


def guard_query(query: str) -> str | None:
    """Return an error message if `query` is not a single read-only statement."""
    if not query or not query.strip():
        return "No SQL query provided"

    statements = [s for s in _sanitize(query).split(";") if s.strip()]

    if not statements:
        return "No SQL query provided"

    # psycopg2 executes every statement passed to execute(), so a second one
    # would run even if only the first were inspected.
    if len(statements) > 1:
        return "Only a single SELECT statement is allowed."

    statement = statements[0].strip()

    if not _READ_PREFIX.match(statement):
        return "Only SELECT statements are allowed."

    if statement.lower().startswith("with") and _CTE_WRITE.search(statement):
        return "Only read-only SELECT statements are allowed."

    return None
