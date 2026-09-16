"""The `debug` block: what it carries, and what it refuses to carry.

A response that explains itself is worth having in a project where the person
calling the API is the person who has to fix it. The risk it introduces is that
the explanation quotes something it shouldn't -- an upstream error message is
uncontrolled text, and connection URLs carry passwords in them -- so these pin
the two limits that make it safe enough to leave on.
"""
import httpx
import pytest
from groq import RateLimitError

from app.core.config import settings
from app.core.errors import _MAX_DEBUG_CHARS, debug_details
from app.query.agent.errors import classify


@pytest.fixture(autouse=True)
def details_on(monkeypatch):
    monkeypatch.setattr(settings, "EXPOSE_ERROR_DETAILS", True)


def test_the_switch_removes_the_key_entirely(monkeypatch):
    """Off means absent, not empty: a caller reading `detail` sees the same two
    keys it always did, so nothing downstream has to special-case a blank."""
    monkeypatch.setattr(settings, "EXPOSE_ERROR_DETAILS", False)

    assert debug_details(ValueError("boom"), "check the thing") == {}


def test_it_names_the_exception_and_quotes_it():
    details = debug_details(ValueError("boom"), "check the thing")["debug"]

    assert details == {"type": "ValueError", "error": "boom", "hint": "check the thing"}


def test_a_hint_alone_is_enough():
    """Some failures are deliberately reported without their exception text --
    a Redis auth error quotes the AUTH command. The hint still travels."""
    assert debug_details(hint="fix REDIS_URL") == {"debug": {"hint": "fix REDIS_URL"}}


def test_nothing_to_say_means_no_key():
    assert debug_details() == {}


@pytest.mark.parametrize(
    "raw",
    [
        "could not connect to postgresql://admin:hunter2@db.example.com:5432/sales",
        "Error 111 connecting to redis://:hunter2@localhost:6379/0",
        "MySQLdb: mysql://root:hunter2@127.0.0.1/app refused",
    ],
)
def test_a_password_in_a_url_never_survives(raw):
    """Drivers quote the URL they were handed, password and all, and a debug
    block is the one thing here that gets pasted into a chat or an issue."""
    details = debug_details(RuntimeError(raw))["debug"]

    assert "hunter2" not in details["error"]
    assert ":***@" in details["error"]


def test_a_url_without_a_password_is_left_alone():
    """Scrubbing that eats the host would cost the block its whole point."""
    details = debug_details(RuntimeError("cannot reach redis://localhost:6379/0"))["debug"]

    assert details["error"] == "cannot reach redis://localhost:6379/0"


def test_a_long_upstream_body_is_cut_short():
    """A provider can answer with a whole document; the response is not the
    place to reprint it."""
    details = debug_details(RuntimeError("x" * (_MAX_DEBUG_CHARS * 3)))["debug"]

    assert len(details["error"]) == _MAX_DEBUG_CHARS


def test_a_model_failure_carries_the_hint_the_log_gets():
    """The rate limit from the report that started this: the message tells the
    person to wait, and the hint tells whoever runs this why they must."""
    # Built the way the SDK builds it: the exception wants the response it came
    # from, and reaches through it for the request.
    response = httpx.Response(429, request=httpx.Request("POST", "https://api.groq.com/v1"))
    error = RateLimitError("Error code: 429", response=response, body=None)
    failure = classify(error)

    details = debug_details(error, failure.operator_hint)["debug"]

    assert failure.code == "MODEL_RATE_LIMITED"
    assert details["type"] == "RateLimitError"
    assert "rate limit" in details["hint"]
