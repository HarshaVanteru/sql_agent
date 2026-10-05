"""The API's behaviour when the session store is gone.

This is the sequence in the report that started this work:

    GET  /api/session   -> 503  Session store unreachable (ConnectionError)
    POST /api/session   -> 503  Session store unreachable (ConnectionError)

That part was already right -- a 503 with a readable body is the correct answer
to "Redis is down". These pin it, so the error handlers in app/core/errors.py
keep doing it.
"""
import pytest
from starlette.testclient import TestClient

from app.core.config import settings
from tests.conftest import UNREACHABLE_REDIS_URL


@pytest.fixture
def client_without_redis(monkeypatch):
    monkeypatch.setattr(settings, "REDIS_URL", UNREACHABLE_REDIS_URL)
    from app.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture
def client(monkeypatch, fake_redis):
    monkeypatch.setattr("app.main.create_client", lambda: fake_redis)
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


def test_starting_a_session_is_503_when_redis_is_down(client_without_redis):
    response = client_without_redis.post("/api/session", json={"name": "Venu"})

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "STORAGE_UNAVAILABLE"


def test_the_503_body_does_not_leak_internals(client_without_redis, monkeypatch):
    """With diagnostics off, no host, no port, no exception type: the detail
    belongs in the log and nowhere else."""
    monkeypatch.setattr(settings, "EXPOSE_ERROR_DETAILS", False)
    body = str(client_without_redis.post("/api/session", json={"name": "Venu"}).json())

    assert "6379" not in body
    assert "ConnectionError" not in body
    assert "debug" not in body


def test_diagnostics_ride_beside_the_message_not_inside_it(client_without_redis, monkeypatch):
    """With them on, what a reader sees is unchanged.

    The point of the `debug` key is that switching it on does not degrade the
    message: the exception type and the upstream's own text go somewhere a
    person will never be shown them by accident.
    """
    monkeypatch.setattr(settings, "EXPOSE_ERROR_DETAILS", True)
    detail = client_without_redis.post("/api/session", json={"name": "Venu"}).json()["detail"]

    assert detail["code"] == "STORAGE_UNAVAILABLE"
    assert "ConnectionError" not in detail["message"]
    assert detail["debug"]["type"] == "ConnectionError"
    assert detail["debug"]["hint"]


def test_reading_a_session_without_a_cookie_is_401_not_503(client):
    """Redis up, no cookie: the caller needs a session, not a retry."""
    response = client.get("/api/session")

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "NO_SESSION"


def test_a_session_round_trips(client):
    created = client.post("/api/session", json={"name": "Venu Reddy"})
    assert created.status_code == 201

    current = client.get("/api/session")
    assert current.status_code == 200
    assert current.json()["name"] == "Venu Reddy"
    assert current.json()["connection_count"] == 0


def test_ending_a_session_clears_it(client):
    client.post("/api/session", json={"name": "Venu"})

    assert client.delete("/api/session").status_code == 204
    assert client.get("/api/session").status_code == 401


def test_validation_errors_name_the_field(client):
    response = client.post("/api/session", json={})

    assert response.status_code == 422
    body = response.json()["detail"]
    assert body["code"] == "VALIDATION_ERROR"
    assert "name" in body["fields"]
