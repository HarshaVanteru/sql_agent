"""POST /api/session/extend, through the real app and a fake Redis."""
from datetime import datetime

import pytest
from starlette.testclient import TestClient


@pytest.fixture
def client(monkeypatch, fake_redis):
    monkeypatch.setattr("app.main.create_client", lambda: fake_redis)
    from app.main import app

    with TestClient(app) as client:
        yield client


def _start(client) -> dict:
    response = client.post("/api/session", json={"name": "Venu"})
    assert response.status_code == 201
    return response.json()


def _at(payload: dict) -> datetime:
    return datetime.fromisoformat(payload["expires_at"])


def test_extend_adds_seven_days_and_get_reflects_it(client):
    started = _start(client)

    response = client.post("/api/session/extend", json={"duration": "7d"})

    assert response.status_code == 200
    extended = response.json()
    assert (_at(extended) - _at(started)).days == 7
    assert client.get("/api/session").json()["expires_at"] == extended["expires_at"]


def test_extend_rejects_an_unknown_duration(client):
    _start(client)
    assert client.post("/api/session/extend", json={"duration": "1y"}).status_code == 422


def test_extend_requires_a_session(client):
    response = client.post("/api/session/extend", json={"duration": "24h"})
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "NO_SESSION"


def test_extend_at_the_maximum_is_a_409(client):
    _start(client)
    assert client.post("/api/session/extend", json={"duration": "30d"}).status_code == 200

    response = client.post("/api/session/extend", json={"duration": "24h"})

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "SESSION_AT_MAX"


def test_session_cookie_outlasts_the_default_day(client):
    response = client.post("/api/session", json={"name": "Venu"})
    assert "Max-Age=2592000" in response.headers["set-cookie"]
