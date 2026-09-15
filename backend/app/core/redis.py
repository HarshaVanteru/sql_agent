"""The Redis client -- the app's only datastore.

One client for the process, opened in the FastAPI lifespan and closed on
shutdown. redis.asyncio pools connections internally, so handlers share this
instance rather than each opening their own.

Nothing here connects eagerly, and that is deliberate: a Redis that is briefly
unreachable should not stop the app from booting. It should make requests fail
politely until Redis is back, which is what the timeouts and retries below are
for, and what the handler in app/core/errors.py turns into a 503.
"""
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
