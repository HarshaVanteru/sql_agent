"""The Redis client -- the app's only datastore.

One client for the process, opened in the FastAPI lifespan and closed on
shutdown. redis.asyncio pools connections internally, so handlers share this
instance rather than each opening their own.

Nothing here connects eagerly, and that is deliberate: a Redis that is briefly
unreachable should not stop the app from booting. It should make requests fail
politely until Redis is back, which is what the timeouts and retries below are
for, and what the handler in app/core/errors.py turns into a 503.
"""
import asyncio
from urllib.parse import urlsplit, urlunsplit

from redis.asyncio import Redis
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from app.core.config import settings


def create_client() -> Redis:
    """Build the client. Nothing connects until the first command is issued."""
    return Redis.from_url(
        settings.REDIS_URL,
        # Everything stored is JSON text, so decoding here keeps the str/bytes
        # juggling out of every call site.
        decode_responses=True,
        # Without these a Redis that accepts connections but never answers --
        # a hung host, a dropped route -- holds the request until the client
        # gives up, which is to say forever.
        socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT,
        socket_timeout=settings.REDIS_TIMEOUT,
        socket_keepalive=True,
        # Notices a connection that died while idle in the pool, rather than
        # handing it to a request to discover.
        health_check_interval=30,
        # A restart or a failover is a blip, not an outage: back off and try
        # again before telling anyone. Bounded, so a real outage still answers
        # quickly instead of hanging on to the request.
        retry=Retry(ExponentialBackoff(base=0.05, cap=0.5), retries=settings.REDIS_RETRIES),
        retry_on_error=[RedisConnectionError, RedisTimeoutError],
    )


def redacted_url(url: str | None = None) -> str:
    """REDIS_URL with any password starred out, safe to put in a log line.

    `redis://:hunter2@host:6379/0` -> `redis://:***@host:6379/0`. Logging the
    URL is worth doing -- "connected" means nothing without saying to what, and
    pointing at the wrong instance is a common enough mistake -- but a
    password-protected Redis carries its password in that same string, and a
    startup banner is exactly the line people paste into an issue.
    """
    raw = settings.REDIS_URL if url is None else url
    parts = urlsplit(raw)
    if parts.password is None:
        return raw
    userinfo = f"{parts.username or ''}:***@"
    host = parts.hostname or ""
    if parts.port:
        host = f"{host}:{parts.port}"
    return urlunsplit((parts.scheme, f"{userinfo}{host}", parts.path, parts.query, parts.fragment))


async def check_connection(
    client: Redis,
    # noqa on the parameter, not the def: an explicit, caller-visible bound is
    # exactly this function's job, so ASYNC109's "use asyncio.timeout at the
    # call site instead" would move the guarantee away from where it is needed.
    timeout: float | None = None,  # noqa: ASYNC109
) -> str | None:
    """PING Redis. None means it answered; otherwise the failure's type name.

    The type is what is worth reporting and the only part that reliably
    survives scrubbing: ConnectionError means it is down, AuthenticationError
    means REDIS_URL is missing a password, TimeoutError means it is reachable
    but not answering.

    Bounded separately from the client's own timeouts because those are
    per-attempt and the client retries: with REDIS_RETRIES=2 a refused
    connection is three attempts plus backoff before it gives up, and startup
    should not sit on that. Callers get an answer or a timeout, not a wait.
    """
    ceiling = timeout if timeout is not None else settings.REDIS_CONNECT_TIMEOUT
    try:
        await asyncio.wait_for(client.ping(), timeout=ceiling)
    except TimeoutError:
        return "TimeoutError"
    except Exception as error:
        # Deliberately broad. A bad REDIS_URL raises ValueError, a DNS failure
        # raises from the socket layer, and neither is a RedisError -- but both
        # mean the same thing to the caller: the store is not usable.
        return type(error).__name__
    return None
