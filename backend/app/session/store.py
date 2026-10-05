"""Redis key layout and the reads/writes over it.

Everything a visitor accumulates -- who they said they are, the databases they
connected, the questions they asked -- hangs off one session id:

    session:{sid}                          JSON  the session itself
    session:{sid}:connections              HASH  connection_id -> connection JSON
    session:{sid}:conversations            HASH  conversation_id -> conversation JSON
    session:{sid}:conv:{conv_id}:messages  LIST  message JSON, oldest first

Every one of those keys is given the *same absolute* expiry, so a session and
everything hanging off it die together at the 24-hour mark rather than leaving
orphaned conversations behind. The expiry is not extended by use: a session is a
visit, and a visit has a length. It moves only when the visitor asks for more
time, through `extend`.

This module owns the key names. Nothing else builds a Redis key by hand.
"""
from __future__ import annotations

import json
import re
import secrets
import time
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta

from redis.asyncio import Redis
from redis.exceptions import WatchError

from app.core.config import settings

_SLUG = re.compile(r"[^a-z0-9]+")


def _slugify(name: str) -> str:
    """A readable, safe stem for the session id: "Venu Reddy" -> "venu-reddy"."""
    slug = _SLUG.sub("-", name.strip().lower()).strip("-")[:24]
    return slug or "guest"


def new_session_id(name: str) -> str:
    """Build a session id from the person's name and the current timestamp.

    The random suffix is what makes it a credential rather than a guess: a name
    and a rough arrival time are both things an attacker can know, and without
    the suffix, knowing them would be enough to read someone else's session.
    """
    return f"{_slugify(name)}-{int(time.time())}-{secrets.token_urlsafe(12)}"


# What a visitor may add to a session, by the name the API uses for it.
EXTENSIONS: dict[str, timedelta] = {
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}

_EXTEND_ATTEMPTS = 5
# The cap moves with the clock, so right after hitting it there is always a few
# milliseconds of headroom. A gain smaller than this is not an extension.
_MIN_GAIN = timedelta(minutes=1)


class SessionAtMaximum(Exception):
    """The session already has as much time left as it is allowed."""


class SessionGone(Exception):
    """The session expired or was ended while the request was being handled."""


@dataclass(frozen=True)
class SessionData:
    sid: str
    name: str
    created_at: datetime
    expires_at: datetime


def _key(sid: str) -> str:
    return f"session:{sid}"


def connections_key(sid: str) -> str:
    return f"session:{sid}:connections"


def conversations_key(sid: str) -> str:
    return f"session:{sid}:conversations"


def messages_key(sid: str, conversation_id: str) -> str:
    return f"session:{sid}:conv:{conversation_id}:messages"


def _deadline(session: SessionData) -> int:
    """The one unix timestamp every key belonging to this session expires at."""
    return int(session.expires_at.timestamp())


def _all_keys(sid: str, conversation_ids: list[str]) -> list[str]:
    return [
        _key(sid),
        connections_key(sid),
        conversations_key(sid),
        *(messages_key(sid, cid) for cid in conversation_ids),
    ]


async def create(redis: Redis, name: str) -> SessionData:
    """Start a session for `name`, expiring SESSION_TTL_SECONDS from now."""
    now = datetime.now(UTC)
    session = SessionData(
        sid=new_session_id(name),
        name=name.strip(),
        created_at=now,
        expires_at=now + timedelta(seconds=settings.SESSION_TTL_SECONDS),
    )
    await redis.set(
        _key(session.sid),
        json.dumps(
            {
                "name": session.name,
                "created_at": session.created_at.isoformat(),
                "expires_at": session.expires_at.isoformat(),
            }
        ),
        # Absolute, not a relative TTL: the side keys are stamped with this same
        # timestamp later, and a relative expiry resolved at command time would
        # land a second or two off it.
        exat=_deadline(session),
    )
    return session


async def get(redis: Redis, sid: str) -> SessionData | None:
    """Load a session, or None if it never existed or has expired."""
    raw = await redis.get(_key(sid))
    if raw is None:
        return None
    data = json.loads(raw)
    return SessionData(
        sid=sid,
        name=data["name"],
        created_at=datetime.fromisoformat(data["created_at"]),
        expires_at=datetime.fromisoformat(data["expires_at"]),
    )


async def touch_expiry(redis: Redis, session: SessionData) -> None:
    """Re-apply the session's deadline to its side keys.

    Redis expiries are per key, and a key created after the session (a new
    conversation, say) has none of its own. Stamping them all with the session's
    absolute deadline is what makes the whole tree vanish at the same moment.
    """
    conversation_ids = await redis.hkeys(conversations_key(session.sid))
    deadline = _deadline(session)
    pipe = redis.pipeline()
    for key in _all_keys(session.sid, list(conversation_ids)):
        pipe.expireat(key, deadline)
    await pipe.execute()


async def extend(redis: Redis, session: SessionData, duration: str) -> SessionData:
    """Add `duration` to the session's expiry, and move every key to match.

    The addition is to the current expiry, so asking for 7 days with 2 left
    leaves 9. Remaining time is capped at SESSION_MAX_LIFETIME_SECONDS from now;
    an extension that would pass the cap is cut to it, and one that would add
    under a minute raises SessionAtMaximum.

    Runs under WATCH on the session key so two extensions racing (two tabs) each
    add their time instead of the later one overwriting the earlier.
    """
    delta = EXTENSIONS[duration]
    key = _key(session.sid)

    async with redis.pipeline() as pipe:
        for _ in range(_EXTEND_ATTEMPTS):
            try:
                await pipe.watch(key)
                current = await get(pipe, session.sid)  # type: ignore[arg-type]  # immediate mode
                if current is None:
                    raise SessionGone
                cap = datetime.now(UTC) + timedelta(seconds=settings.SESSION_MAX_LIFETIME_SECONDS)
                new_expiry = min(current.expires_at + delta, cap)
                if new_expiry - current.expires_at < _MIN_GAIN:
                    raise SessionAtMaximum

                extended = replace(current, expires_at=new_expiry)
                conversation_ids = list(await pipe.hkeys(conversations_key(session.sid)))
                deadline = _deadline(extended)

                pipe.multi()
                pipe.set(
                    key,
                    json.dumps(
                        {
                            "name": extended.name,
                            "created_at": extended.created_at.isoformat(),
                            "expires_at": extended.expires_at.isoformat(),
                        }
                    ),
                    exat=deadline,
                )
                for side_key in _all_keys(session.sid, conversation_ids)[1:]:
                    pipe.expireat(side_key, deadline)
                await pipe.execute()
                return extended
            except WatchError:
                continue
    raise RuntimeError("Could not extend the session: it kept changing underneath us.")


async def destroy(redis: Redis, sid: str) -> None:
    """Delete a session and everything hanging off it."""
    conversation_ids = await redis.hkeys(conversations_key(sid))
    await redis.delete(*_all_keys(sid, list(conversation_ids)))
