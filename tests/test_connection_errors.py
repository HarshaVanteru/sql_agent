"""Tests for turning driver errors into messages a user can act on.

These strings are what pymysql and psycopg2 actually raise; the point is that a
user reading the message can tell what to fix.
"""
import pytest

from backend.query.databases.connections import (
    connection_error_message,
    dialect_label,
)

HOST, PORT = "db.example.com", 3306


def msg(db_type, error_text, host=HOST, port=PORT):
    return connection_error_message(db_type, Exception(error_text), host, port)


# --- MySQL -----------------------------------------------------------------


def test_mysql_bad_password():
    assert msg("mysql", '(1045, "Access denied for user \'bob\'@\'localhost\'")') == (
        "Invalid username or password"
    )


def test_mysql_unknown_database():
    assert msg("mysql", "(1049, \"Unknown database 'nope'\")") == "Database does not exist"


def test_mysql_unreachable_host_names_the_host_not_gibberish():
    """The old message dug the host out of the error text by splitting on "on",
    which also matches the "on" inside "connect" -- producing
    "Cannot connect to MySQL server at nect to mysql server".
    """
    real = "(2003, \"Can't connect to MySQL server on 'db.example.com' ([Errno 111] Connection refused)\")"
    assert msg("mysql", real) == "Cannot connect to MySQL server at db.example.com:3306"


def test_mysql_timeout():
    assert msg("mysql", "connection timeout expired") == (
        "Connection timeout - server not responding"
    )


def test_mysql_unknown_error_falls_back_to_the_driver_text():
    assert msg("mysql", "Something odd (details)").startswith("Connection failed:")


# --- PostgreSQL ------------------------------------------------------------


def test_postgres_bad_password():
    assert msg(
        "postgresql", 'FATAL:  password authentication failed for user "bob"'
    ) == "Invalid username or password"


def test_postgres_unknown_database():
    assert msg("postgresql", 'FATAL:  database "nope" does not exist') == (
        "Database does not exist"
    )


def test_postgres_missing_role_is_not_reported_as_a_missing_database():
    # "does not exist" alone must not win: this is an auth problem.
    out = msg("postgresql", 'FATAL:  role "bob" does not exist')
    assert out != "Database does not exist"


def test_postgres_bad_hostname():
    assert msg(
        "postgresql", 'could not translate host name "nope" to address'
    ) == "Invalid hostname - cannot resolve address"


def test_postgres_connection_refused_names_host_and_port():
    assert msg(
        "postgresql", "could not connect to server: Connection refused", port=5432
    ) == "Cannot connect to PostgreSQL server at db.example.com:5432"


# --- shared ----------------------------------------------------------------


@pytest.mark.parametrize(
    "db_type, expected", [("mysql", "MySQL"), ("postgresql", "PostgreSQL"), ("MySQL", "MySQL")]
)
def test_dialect_label(db_type, expected):
    assert dialect_label(db_type) == expected
