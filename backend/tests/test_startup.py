"""What the app says at startup, and whether it is true.

The bug these cover: the lifespan built the Redis client and immediately logged
"Connected to Redis at ...". The client is lazy by design -- `create_client`
opens no socket -- so that line was printed whether or not Redis was there. A
server with Redis down booted announcing a healthy connection and then answered
503 to everything, which is a long way from the log line that would have said
why.
"""
from starlette.testclient import TestClient

from app.core.config import settings
from tests.conftest import UNREACHABLE_REDIS_URL


def _startup_messages(logged: list[tuple[str, str]]) -> str:
    return "\n".join(template for _level, template in logged)


def test_does_not_claim_a_connection_it_never_made(monkeypatch, logged):
    """Redis down: the app must not report that it connected."""
    monkeypatch.setattr(settings, "REDIS_URL", UNREACHABLE_REDIS_URL)
    from app.main import app

    with TestClient(app):
        pass

    assert "Connected to Redis" not in _startup_messages(logged)


def test_reports_the_failure_when_redis_is_down(monkeypatch, logged):
    """And it must say so, at a level someone watching the log will notice."""
    monkeypatch.setattr(settings, "REDIS_URL", UNREACHABLE_REDIS_URL)
    from app.main import app

    with TestClient(app):
        pass

    errors = [template for level, template in logged if level in ("error", "warning")]
    assert any("Redis" in template for template in errors), logged


def test_still_boots_with_redis_down(monkeypatch, logged):
    """Booting anyway is deliberate: a blip should not stop the process coming up."""
    monkeypatch.setattr(settings, "REDIS_URL", UNREACHABLE_REDIS_URL)
    from app.main import app

    with TestClient(app) as client:
        assert client.get("/health").status_code == 200


def test_confirms_a_connection_that_really_is_there(monkeypatch, logged, fake_redis):
    """Redis up: the claim is made, because now it has been checked."""
    monkeypatch.setattr("app.main.create_client", lambda: fake_redis)
    from app.main import app

    with TestClient(app):
        pass

    assert "Connected to Redis" in _startup_messages(logged)


def test_startup_log_does_not_leak_the_redis_password(monkeypatch, logged, fake_redis):
    """A REDIS_URL with a password in it is logged redacted."""
    monkeypatch.setattr(settings, "REDIS_URL", "redis://:hunter2@localhost:6379/0")
    monkeypatch.setattr("app.main.create_client", lambda: fake_redis)
    from app.main import app

    with TestClient(app):
        pass

    assert "hunter2" not in str(logged)
