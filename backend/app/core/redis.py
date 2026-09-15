"""The Redis client -- the app's only datastore.

One client for the process, opened in the FastAPI lifespan and closed on
shutdown. redis.asyncio pools connections internally, so handlers share this
instance rather than each opening their own.
"""
from redis.asyncio import Redis

from app.core.config import settings


def create_client() -> Redis:
    """Build the client. Nothing connects until the first command is issued."""
    return Redis.from_url(
        settings.REDIS_URL,
        # Everything stored is JSON text, so decoding here keeps the str/bytes
        # juggling out of every call site.
        decode_responses=True,
        health_check_interval=30,
    )
