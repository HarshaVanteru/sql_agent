"""Read-only, single-database guard for SQL.

Shared by the direct query pipeline and the agent's run_query tool. Any path
that puts SQL in front of a user's database must go through guard_query first.

The guard enforces two things:
  1. Read-only: a single SELECT (or a CTE that resolves to one), nothing that
     writes, and nothing that reads or writes files on the database host.
  2. One database: the query may not reach other databases or the server's
     system schemas. A connection is opened against one database, but that is
     only a default -- MySQL will happily resolve `otherdb.table`, and both
     engines expose catalogs like information_schema. Cross-database and
     system-schema references are rejected here.

This is defence in depth. The real boundary is a least-privilege database user
granted access to only the one database; the guard cannot be a substitute for
that, because SQL is not fully parseable with regular expressions. It closes the
obvious holes and keeps an honest user's mistakes from leaking across databases.
"""
import re

# A valid query is a single read: a SELECT, or a CTE that resolves to one.
_READ_PREFIX = re.compile(r"^(?:select|with)\b", re.IGNORECASE)

# Postgres allows data-modifying statements inside a CTE, which a bare
# "starts with WITH" check would wave through:
#   WITH x AS (DELETE FROM users RETURNING *) SELECT * FROM x
_CTE_WRITE = re.compile(r"\b(?:insert|update|delete|merge)\b", re.IGNORECASE)

# MySQL writes query results to a file on the DB host:
#   SELECT * FROM users INTO OUTFILE '/var/www/dump.csv'
_INTO_FILE = re.compile(r"\binto\s+(?:out|dump)file\b", re.IGNORECASE)

# Functions that read/write host files or reach other servers, all callable
# from inside a plain SELECT.
_DANGEROUS_FUNC = re.compile(
    r"\b(?:load_file|pg_read_file|pg_read_binary_file|pg_ls_dir|pg_stat_file"
    r"|lo_import|lo_export|dblink|dblink_connect)\s*\(",
    re.IGNORECASE,
)

# Server-wide catalogs and the built-in databases. Referencing any as a
# qualifier (`information_schema.tables`, `mysql.user`) enumerates or reads
# outside the selected database. The agent has list_tables/describe_table for
# legitimate schema questions, so these are never needed here.
_SYSTEM_SCHEMA = re.compile(
    r"\b(?:information_schema|performance_schema|mysql|sys|pg_catalog|pg_toast)\s*\.",
    re.IGNORECASE,
)

# A table reference qualified by a database: the identifier right after FROM or
# JOIN, followed by a dot (`FROM sales.orders`). Column qualifiers (`o.total`)
# never sit in this position, so this does not catch them.
_FROM_JOIN_QUALIFIER = re.compile(
    r"\b(?:from|join)\s+([A-Za-z_]\w*)\s*\.", re.IGNORECASE
)

# A three-part name (`db.table.column`): in MySQL the leading part is a
# database. Legitimate app queries qualify by table or alias, not database.
_THREE_PART = re.compile(
    r"\b([A-Za-z_]\w*)\s*\.\s*[A-Za-z_]\w*\s*\.\s*[A-Za-z_]\w*"
)


def _normalize(query: str, dialect: str | None = None) -> str:
    """Blank comments and string literals; unwrap quoted identifiers.

    The checks below inspect keywords and identifiers, so string contents must
    be gone (a literal must not read as a keyword or a schema name) while quoted
    identifiers must survive *unquoted* -- otherwise ``\\`mysql\\`.\\`user\\```
    would slip past the schema check simply by being backtick-quoted.

    In MySQL's default mode a double-quoted span is a string; everywhere else it
    is a quoted identifier.
    """
    double_is_string = dialect == "mysql"
    out: list[str] = []
    i, n = 0, len(query)

    while i < n:
        ch = query[i]

        # String literal -> blank it out entirely.
        if ch == "'" or (ch == '"' and double_is_string):
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

        # Quoted identifier -> drop the quotes, keep the name so it stays visible
        # to the schema/qualifier checks.
        if ch == "`" or (ch == '"' and not double_is_string):
            quote = ch
            i += 1
            while i < n:
                if query[i] == quote:
                    if i + 1 < n and query[i + 1] == quote:  # "" escapes a quote
                        out.append(query[i])
                        i += 2
                        continue
                    i += 1
                    break
                out.append(query[i])
                i += 1
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


def guard_query(
    query: str,
    *,
    dialect: str | None = None,
    database_name: str | None = None,
) -> str | None:
    """Return an error message if `query` is not a safe, single-database read.

    `dialect` ("mysql" / "postgresql") and `database_name` enable the
    cross-database checks. Omitting them keeps the read-only checks only.
    """
    if not query or not query.strip():
        return "No SQL query provided"

    norm = _normalize(query, dialect)
    statements = [s for s in norm.split(";") if s.strip()]

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

    if _INTO_FILE.search(statement):
        return "Writing query results to a file is not allowed."

    if _DANGEROUS_FUNC.search(statement):
        return "File and cross-server functions are not allowed."

    if _SYSTEM_SCHEMA.search(statement):
        return "Access to system schemas is not allowed."

    # Cross-database references only mean anything on MySQL, where a connection
    # can resolve `otherdb.table`. Postgres cannot cross databases in a single
    # connection, so a schema qualifier there is same-database and left alone.
    if dialect == "mysql" and database_name:
        allowed = database_name.lower()

        qualifier = next(
            (
                m.group(1)
                for m in _FROM_JOIN_QUALIFIER.finditer(statement)
                if m.group(1).lower() != allowed
            ),
            None,
        )
        if qualifier is None:
            qualifier = next(
                (
                    m.group(1)
                    for m in _THREE_PART.finditer(statement)
                    if m.group(1).lower() != allowed
                ),
                None,
            )
        if qualifier is not None:
            return (
                f"Queries may only reference the '{database_name}' database; "
                f"'{qualifier}' is not allowed."
            )

    return None
