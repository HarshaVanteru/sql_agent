"""The Redis key layout and the invariant that holds it together.

The invariant worth testing: a session and every key hanging off it carry the
*same absolute* deadline, so the whole tree dies at one moment rather than
leaving orphaned conversations behind a session that is already gone.
"""
import pytest

from app.core.config import settings
from app.session import store

pytestmark = pytest.mark.anyio


async def test_create_returns_a_session_that_reads_back(fake_redis):
    created = await store.create(fake_redis, "Venu Reddy")
    loaded = await store.get(fake_redis, created.sid)

    assert loaded is not None
    assert loaded.name == "Venu Reddy"
    assert loaded.sid == created.sid
    # Round-tripped through JSON, so this is the assertion that catches a
    # format change on either side.
    assert loaded.created_at == created.created_at
    assert loaded.expires_at == created.expires_at


async def test_missing_session_is_none_not_an_error(fake_redis):
    assert await store.get(fake_redis, "nobody-1234-xxxx") is None


async def test_session_id_is_not_guessable(fake_redis):
    """A name and a rough arrival time are both things an attacker can know."""
    first = await store.create(fake_redis, "Venu Reddy")
    second = await store.create(fake_redis, "Venu Reddy")

    assert first.sid != second.sid
    assert first.sid.startswith("venu-reddy-")


@pytest.mark.parametrize(
    ("name", "stem"),
    [
        ("Venu Reddy", "venu-reddy"),
        ("  Ada  ", "ada"),
        ("!!!", "guest"),
        ("", "guest"),
        ("A" * 100, "a" * 24),
    ],
)
async def test_session_id_stem(fake_redis, name: str, stem: str):
    from app.session.store import new_session_id

    assert new_session_id(name).startswith(f"{stem}-")


async def test_session_key_expires_with_the_session(fake_redis):
    created = await store.create(fake_redis, "Venu")
    ttl = await fake_redis.ttl(f"session:{created.sid}")

    assert 0 < ttl <= settings.SESSION_TTL_SECONDS


async def test_side_keys_share_the_session_deadline(fake_redis):
    """A conversation created later has no expiry of its own until it is stamped."""
    session = await store.create(fake_redis, "Venu")
    await fake_redis.hset(store.connections_key(session.sid), "c1", "{}")
    await fake_redis.hset(store.conversations_key(session.sid), "v1", "{}")
    await fake_redis.rpush(store.messages_key(session.sid, "v1"), "{}")

    # Before touch_expiry, the side keys outlive the session -- -1 is "no TTL".
    assert await fake_redis.ttl(store.connections_key(session.sid)) == -1

    await store.touch_expiry(fake_redis, session)

    deadline = int(session.expires_at.timestamp())
    for key in (
        f"session:{session.sid}",
        store.connections_key(session.sid),
        store.conversations_key(session.sid),
        store.messages_key(session.sid, "v1"),
    ):
        assert await fake_redis.expiretime(key) == deadline, key


async def test_destroy_removes_the_whole_tree(fake_redis):
    session = await store.create(fake_redis, "Venu")
    await fake_redis.hset(store.conversations_key(session.sid), "v1", "{}")
    await fake_redis.rpush(store.messages_key(session.sid, "v1"), "{}")

    await store.destroy(fake_redis, session.sid)

    assert await store.get(fake_redis, session.sid) is None
    assert await fake_redis.exists(store.conversations_key(session.sid)) == 0
    assert await fake_redis.exists(store.messages_key(session.sid, "v1")) == 0


async def _session_with_children(fake_redis):
    session = await store.create(fake_redis, "Venu")
    await fake_redis.hset(store.connections_key(session.sid), "c1", "{}")
    await fake_redis.hset(store.conversations_key(session.sid), "v1", "{}")
    await fake_redis.rpush(store.messages_key(session.sid, "v1"), "{}")
    await store.touch_expiry(fake_redis, session)
    return session


@pytest.mark.parametrize(("duration", "days"), [("24h", 1), ("7d", 7), ("30d", 30)])
async def test_extend_adds_to_the_current_expiry(fake_redis, monkeypatch, duration, days):
    # Room under the cap for every option, so none is clamped.
    monkeypatch.setattr(settings, "SESSION_MAX_LIFETIME_SECONDS", 100 * 86_400)
    session = await _session_with_children(fake_redis)

    extended = await store.extend(fake_redis, session, duration)

    assert extended.expires_at - session.expires_at == store.EXTENSIONS[duration]
    assert extended.expires_at - session.expires_at == __import__("datetime").timedelta(days=days)
    loaded = await store.get(fake_redis, session.sid)
    assert loaded is not None and loaded.expires_at == extended.expires_at


async def test_extend_moves_every_key_to_the_same_new_deadline(fake_redis):
    session = await _session_with_children(fake_redis)

    extended = await store.extend(fake_redis, session, "7d")

    deadline = int(extended.expires_at.timestamp())
    for key in (
        f"session:{session.sid}",
        store.connections_key(session.sid),
        store.conversations_key(session.sid),
        store.messages_key(session.sid, "v1"),
    ):
        assert await fake_redis.expiretime(key) == deadline, key


async def test_extend_is_clamped_to_the_maximum_lifetime(fake_redis):
    session = await _session_with_children(fake_redis)

    extended = await store.extend(fake_redis, session, "30d")  # 24h + 30d > 30d

    cap_seconds = settings.SESSION_MAX_LIFETIME_SECONDS
    remaining = (extended.expires_at - session.created_at).total_seconds()
    assert remaining <= cap_seconds + 5
    assert extended.expires_at > session.expires_at


async def test_extend_at_the_maximum_raises(fake_redis):
    session = await _session_with_children(fake_redis)
    await store.extend(fake_redis, session, "30d")  # now at the cap
    current = await store.get(fake_redis, session.sid)
    assert current is not None

    with pytest.raises(store.SessionAtMaximum):
        await store.extend(fake_redis, current, "24h")


async def test_extend_of_an_ended_session_raises_gone(fake_redis):
    session = await store.create(fake_redis, "Venu")
    await store.destroy(fake_redis, session.sid)

    with pytest.raises(store.SessionGone):
        await store.extend(fake_redis, session, "24h")
