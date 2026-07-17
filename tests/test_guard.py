"""Tests for the read-only, single-database SQL guard.

The guard is the last thing between a user's SQL and their database, so its
failure modes are security bugs rather than ordinary ones. Every case here is
something someone could actually send: the point is not coverage of the regexes
but of the ways a write, a file read, or a second statement could slip through.

A returned message means rejected; None means allowed.
"""
import pytest

from backend.query.guard import guard_query


def rejected(query: str, **kwargs) -> bool:
    return guard_query(query, **kwargs) is not None


def allowed(query: str, **kwargs) -> bool:
    return guard_query(query, **kwargs) is None


# --- the happy path: ordinary reads must keep working ----------------------


@pytest.mark.parametrize(
    "query",
    [
        "SELECT * FROM users",
        "select id, name from users where active = 1",
        "SELECT * FROM orders ORDER BY total DESC LIMIT 10",
        "SELECT COUNT(*) FROM users",
        "SELECT * FROM users;",  # a single trailing semicolon is still one statement
        "  \n SELECT 1 \n ",
        "WITH recent AS (SELECT * FROM orders WHERE created_at > '2024-01-01') SELECT * FROM recent",
        "SELECT o.total, c.name FROM orders o JOIN customers c ON c.id = o.customer_id",
        "SELECT * FROM users WHERE note = 'delete from users'",  # a write only inside a literal
    ],
)
def test_allows_ordinary_reads(query):
    assert allowed(query), f"should be allowed: {query!r}"


# --- writes ----------------------------------------------------------------


@pytest.mark.parametrize(
    "query",
    [
        "INSERT INTO users (name) VALUES ('x')",
        "UPDATE users SET name = 'x'",
        "DELETE FROM users",
        "DROP TABLE users",
        "TRUNCATE TABLE users",
        "ALTER TABLE users ADD COLUMN x INT",
        "CREATE TABLE t (id INT)",
        "GRANT ALL ON *.* TO 'x'@'%'",
        "REPLACE INTO users VALUES (1)",
        "  delete from users  ",
        "-- a comment\nDELETE FROM users",  # the comment must not hide the write
    ],
)
def test_rejects_writes(query):
    assert rejected(query), f"should be rejected: {query!r}"


def test_rejects_write_hidden_in_cte():
    # Postgres allows data-modifying statements inside a CTE, which a bare
    # "starts with WITH" check would wave through.
    assert rejected("WITH x AS (DELETE FROM users RETURNING *) SELECT * FROM x")
    assert rejected("WITH x AS (INSERT INTO t VALUES (1) RETURNING *) SELECT * FROM x")
    assert rejected("WITH x AS (UPDATE users SET a = 1 RETURNING *) SELECT * FROM x")


# --- statement smuggling ---------------------------------------------------


@pytest.mark.parametrize(
    "query",
    [
        "SELECT 1; DROP TABLE users",
        "SELECT 1; SELECT 2",
        "SELECT * FROM users; DELETE FROM users",
    ],
)
def test_rejects_multiple_statements(query):
    assert rejected(query), f"should be rejected: {query!r}"


def test_semicolon_inside_a_literal_is_not_a_statement_break():
    assert allowed("SELECT * FROM users WHERE note = 'a;b'")


def test_semicolon_inside_a_comment_is_not_a_statement_break():
    assert allowed("SELECT 1 -- ; DROP TABLE users")
    assert allowed("SELECT /* ; DROP TABLE users */ 1")


def test_postgres_backslash_does_not_escape_a_quote():
    """A backslash is an ordinary character in a standard Postgres literal.

    With standard_conforming_strings on (the default since 9.1) `'a\\'` ends at
    the second quote, so treating the backslash as an escape would let the rest
    of the line -- a second statement -- hide inside what looks like a string.
    psycopg2 executes every statement it is given, so this must be rejected.
    """
    attack = r"SELECT 'a\'; DROP TABLE users; --'"
    assert rejected(attack, dialect="postgresql", database_name="shop")


def test_mysql_backslash_does_escape_a_quote():
    """MySQL honours backslash escapes, so the same text really is one literal."""
    attack = r"SELECT 'a\'; DROP TABLE users; --'"
    assert allowed(attack, dialect="mysql", database_name="shop")


def test_postgres_e_string_does_escape_a_quote():
    """E'...' is the one Postgres literal where a backslash escapes the quote."""
    assert allowed(r"SELECT E'a\'; DROP TABLE users; --'", dialect="postgresql")
    assert allowed(r"SELECT e'a\'; DROP TABLE users; --'", dialect="postgresql")


def test_identifier_ending_in_e_is_not_an_escape_string():
    # `code'...'` is not valid SQL, but the E-string check must key off a real
    # prefix rather than any trailing "e", or a literal could be over-read.
    assert rejected(r"SELECT * FROM code'a\'; DROP TABLE users; --'", dialect="postgresql")


def test_mysql_backslash_escapes_inside_double_quoted_strings():
    # In MySQL "..." is a string and backslashes escape there too.
    assert allowed(r'SELECT "a\"; DROP TABLE users; --"', dialect="mysql")


def test_postgres_dollar_quoting_is_not_mistaken_for_a_read():
    # Fails closed: the guard does not parse dollar quoting, and must not let a
    # second statement through because of it.
    assert rejected("SELECT $$x$$; DROP TABLE users", dialect="postgresql")


# --- reading and writing host files ----------------------------------------


@pytest.mark.parametrize(
    "query",
    [
        "SELECT * FROM users INTO OUTFILE '/var/www/dump.csv'",
        "SELECT * FROM users INTO DUMPFILE '/tmp/x'",
        "select * from t into   outfile '/tmp/x'",
    ],
)
def test_rejects_writing_results_to_a_file(query):
    assert rejected(query), f"should be rejected: {query!r}"


@pytest.mark.parametrize(
    "query",
    [
        "SELECT load_file('/etc/passwd')",
        "SELECT pg_read_file('/etc/passwd')",
        "SELECT pg_read_binary_file('/etc/passwd')",
        "SELECT pg_ls_dir('/')",
        "SELECT pg_stat_file('/etc/passwd')",
        "SELECT lo_import('/etc/passwd')",
        "SELECT lo_export(1, '/tmp/x')",
        "SELECT dblink('host=evil', 'SELECT 1')",
        "SELECT LOAD_FILE ('/etc/passwd')",  # whitespace before the paren
    ],
)
def test_rejects_file_and_cross_server_functions(query):
    assert rejected(query), f"should be rejected: {query!r}"


# --- system schemas --------------------------------------------------------


@pytest.mark.parametrize(
    "query",
    [
        "SELECT * FROM information_schema.tables",
        "SELECT * FROM INFORMATION_SCHEMA.COLUMNS",
        "SELECT * FROM mysql.user",
        "SELECT * FROM performance_schema.threads",
        "SELECT * FROM sys.host_summary",
        "SELECT * FROM pg_catalog.pg_tables",
        "SELECT * FROM pg_toast.x",
        "SELECT 1 UNION SELECT * FROM information_schema.tables",
    ],
)
def test_rejects_system_schemas(query):
    assert rejected(query), f"should be rejected: {query!r}"


def test_rejects_system_schema_hidden_behind_quoted_identifiers():
    # Quoting must not be an escape hatch: the name has to stay visible.
    assert rejected("SELECT * FROM `mysql`.`user`", dialect="mysql")
    assert rejected('SELECT * FROM "information_schema"."tables"', dialect="postgresql")


def test_system_schema_name_inside_a_literal_is_harmless():
    assert allowed("SELECT * FROM users WHERE note = 'information_schema.tables'")


def test_mysql_double_quotes_are_a_string_not_an_identifier():
    # In MySQL's default mode "..." is a string, so this is a literal, not a table.
    assert allowed('SELECT "information_schema.tables" AS x', dialect="mysql")


# --- cross-database access -------------------------------------------------


def test_rejects_other_database_on_mysql():
    assert rejected(
        "SELECT * FROM otherdb.users", dialect="mysql", database_name="shop"
    )
    assert rejected(
        "SELECT * FROM orders o JOIN otherdb.customers c ON c.id = o.customer_id",
        dialect="mysql",
        database_name="shop",
    )


def test_rejects_three_part_name_on_mysql():
    assert rejected(
        "SELECT otherdb.users.name FROM users", dialect="mysql", database_name="shop"
    )


def test_allows_qualifying_with_the_connected_database():
    assert allowed("SELECT * FROM shop.users", dialect="mysql", database_name="shop")
    assert allowed("SELECT * FROM SHOP.users", dialect="mysql", database_name="shop")


def test_allows_column_and_alias_qualifiers():
    # `o.total` sits in a different position than a database qualifier.
    assert allowed(
        "SELECT o.total FROM orders o WHERE o.id = 1",
        dialect="mysql",
        database_name="shop",
    )


def test_postgres_schema_qualifier_is_same_database():
    # Postgres cannot cross databases in one connection, so `public.users` is fine.
    assert allowed(
        "SELECT * FROM public.users", dialect="postgresql", database_name="shop"
    )


def test_cross_database_message_names_the_offender():
    msg = guard_query("SELECT * FROM otherdb.users", dialect="mysql", database_name="shop")
    assert msg is not None
    assert "otherdb" in msg and "shop" in msg


# --- empty input -----------------------------------------------------------


@pytest.mark.parametrize("query", ["", "   ", "\n\t", ";", ";;"])
def test_rejects_empty_queries(query):
    assert rejected(query), f"should be rejected: {query!r}"
