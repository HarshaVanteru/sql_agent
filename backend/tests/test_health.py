"""Liveness and readiness.

These are two different questions and used to be one answer. `/health` returned
200 with `{"status": "degraded"}` when Redis was down, which meant the Docker
HEALTHCHECK (`curl -fsS /health`) passed either way: the container reported
healthy through a total outage of the only datastore it has.
"""
import pytest
from starlette.testclient import TestClient

from app.core.config import settings
from tests.conftest import UNREACHABLE_REDIS_URL


@pytest.fixture
def client_with_redis(monkeypatch, fake_redis):
    monkeypatch.setattr("app.main.create_client", lambda: fake_redis)
    from app.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture
def client_without_redis(monkeypatch):
    monkeypatch.setattr(settings, "REDIS_URL", UNREACHABLE_REDIS_URL)
    from app.main import app

    with TestClient(app) as client:
        yield client


def test_liveness_is_200_when_redis_is_up(client_with_redis):
    response = client_with_redis.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_liveness_is_200_when_redis_is_down(client_without_redis):
    """The process is alive. Restarting it would not bring Redis back."""
    assert client_without_redis.get("/health").status_code == 200


def test_readiness_is_200_when_redis_is_up(client_with_redis):
    response = client_with_redis.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "redis": "ok"}


def test_readiness_is_503_when_redis_is_down(client_without_redis):
    """This is the one that has to fail, so traffic stops arriving."""
    response = client_without_redis.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "not ready"


def test_readiness_names_the_failure(client_without_redis):
    """The exception type distinguishes 'down' from 'wrong password'."""
    assert response_type(client_without_redis) == "ConnectionError"


def response_type(client) -> str:
    return client.get("/health/ready").json()["redis"]


def test_readiness_recovers_without_a_restart(monkeypatch, fake_redis):
    """Checked live, so Redis coming back is noticed on the next call."""
    monkeypatch.setattr(settings, "REDIS_URL", UNREACHABLE_REDIS_URL)
    from app.main import app

    with TestClient(app) as client:
        assert client.get("/health/ready").status_code == 503
        # Redis comes back.
        app.state.redis = fake_redis
        assert client.get("/health/ready").status_code == 200
