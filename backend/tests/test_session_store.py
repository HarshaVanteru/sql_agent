"""Tests for the session store: identity, key layout, and the 24-hour deadline.

The store is what stands in for auth here -- a session id is the only thing
separating one visitor's connected databases from another's -- so guessability
and expiry are the parts worth pinning down.
"""
import json
import time
from datetime import timedelta

import fakeredis.aioredis
import pytest

from app.session import store


@pytest.fixture
def redis():
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


# ─── Session ids ─────────────────────────────────────────────────────────────

def test_id_carries_the_name_and_a_timestamp():
    before = int(time.time())
    sid = store.new_session_id("Venu Reddy")
    slug, timestamp, suffix = sid.split("-", 1)[0], sid.split("-")[2], sid.split("-")[-1]

    assert sid.startswith("venu-reddy-")
    assert before <= int(timestamp) <= int(time.time())
    assert suffix


@pytest.mark.parametrize(
    "name, expected",
    [
        ("Venu Reddy", "venu-reddy"),
        ("  Aisha  ", "aisha"),
        ("O'Brien", "o-brien"),
        ("李雷", "guest"),          # nothing survives slugging
        ("!!!", "guest"),
        ("x" * 80, "x" * 24),       # capped, so the key stays a sane length
    ],
)
def test_slug_is_derived_from_the_name(name, expected):
    assert store.new_session_id(name).startswith(f"{expected}-")


def test_ids_are_not_guessable_from_name_and_time():
    """Two visitors with the same name in the same second get different ids.

    Without the random suffix, knowing someone's name and roughly when they
    arrived would be enough to read their session.
    """
    ids = {store.new_session_id("Venu") for _ in range(100)}
    assert len(ids) == 100


# ─── Lifecycle ───────────────────────────────────────────────────────────────

async def test_create_then_get_round_trips(redis):
    created = await store.create(redis, "  Venu  ")

    loaded = await store.get(redis, created.sid)
    assert loaded == created
    assert loaded.name == "Venu"  # stored trimmed


async def test_session_expires_24_hours_after_creation(redis):
    session = await store.create(redis, "Venu")

    assert session.expires_at - session.created_at == timedelta(hours=24)
    ttl = await redis.ttl(f"session:{session.sid}")
    assert 86_390 < ttl <= 86_400


async def test_unknown_session_is_none(redis):
    assert await store.get(redis, "nobody-0-xxxx") is None


async def test_expired_session_is_none(redis):
    session = await store.create(redis, "Venu")
    await redis.delete(f"session:{session.sid}")  # what the TTL does, on demand

    assert await store.get(redis, session.sid) is None


# ─── The whole tree shares one deadline ──────────────────────────────────────

async def test_side_keys_inherit_the_session_deadline(redis):
    """A conversation created on hour 23 must still die with the session.

    Side keys are created after the session and have no expiry of their own, so
    without this they would outlive it and leak.
    """
    session = await store.create(redis, "Venu")
    await redis.hset(store.connections_key(session.sid), "c1", json.dumps({"name": "db"}))
    await redis.hset(store.conversations_key(session.sid), "v1", json.dumps({"title": "q"}))
    await redis.rpush(store.messages_key(session.sid, "v1"), json.dumps({"role": "user"}))
    assert await redis.ttl(store.connections_key(session.sid)) == -1  # no expiry yet

    await store.touch_expiry(redis, session)

    deadline = int(session.expires_at.timestamp())
    for key in (
        store.connections_key(session.sid),
        store.conversations_key(session.sid),
        store.messages_key(session.sid, "v1"),
    ):
        assert await redis.expiretime(key) == deadline


async def test_touch_expiry_does_not_extend_the_session(redis):
    """Activity must not buy more time: the session is a visit, not a lease."""
    session = await store.create(redis, "Venu")
    original = await redis.expiretime(f"session:{session.sid}")

    await store.touch_expiry(redis, session)

    assert await redis.expiretime(f"session:{session.sid}") == original


async def test_destroy_removes_the_whole_tree(redis):
    session = await store.create(redis, "Venu")
    await redis.hset(store.connections_key(session.sid), "c1", "{}")
    await redis.hset(store.conversations_key(session.sid), "v1", "{}")
    await redis.rpush(store.messages_key(session.sid, "v1"), "{}")

    await store.destroy(redis, session.sid)

    assert await redis.keys(f"session:{session.sid}*") == []
