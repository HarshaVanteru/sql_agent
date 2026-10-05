"""The Redis helpers: URL redaction and the connection check."""
import pytest

from app.core.redis import check_connection, create_client, redacted_url
from tests.conftest import UNREACHABLE_REDIS_URL

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        # Nothing to hide: returned unchanged.
        ("redis://localhost:6379/0", "redis://localhost:6379/0"),
        ("redis://cache:6379", "redis://cache:6379"),
        # The shape redis-py wants for a password-only Redis.
        ("redis://:hunter2@localhost:6379/0", "redis://:***@localhost:6379/0"),
        # With a username (Redis 6 ACLs), the username is not the secret.
        ("rediss://admin:s3cret@r.example.com:6380/1", "rediss://admin:***@r.example.com:6380/1"),
    ],
)
def test_redacted_url(url: str, expected: str):
    assert redacted_url(url) == expected


def test_redaction_keeps_the_part_that_identifies_the_instance():
    """Pointing at the wrong Redis is the mistake this log line exists to catch."""
    redacted = redacted_url("redis://:pw@cache.internal:6379/3")
    assert "cache.internal" in redacted
    assert "6379" in redacted
    assert "/3" in redacted


async def test_check_connection_returns_none_when_redis_answers(fake_redis):
    assert await check_connection(fake_redis) is None


async def test_check_connection_names_a_refused_connection():
    client = create_client_for(UNREACHABLE_REDIS_URL)
    try:
        assert await check_connection(client, timeout=2.0) == "ConnectionError"
    finally:
        await client.aclose()


async def test_check_connection_is_bounded(fake_redis, monkeypatch):
    """A Redis that accepts the socket and never answers must not hang startup."""
    import asyncio

    async def never_answers():
        await asyncio.sleep(30)

    monkeypatch.setattr(fake_redis, "ping", never_answers)
    assert await check_connection(fake_redis, timeout=0.05) == "TimeoutError"


def create_client_for(url: str):
    from app.core.config import settings

    original = settings.REDIS_URL
    settings.REDIS_URL = url
    try:
        return create_client()
    finally:
        settings.REDIS_URL = original
