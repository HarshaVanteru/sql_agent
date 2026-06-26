"""Clear rate limit cache from Redis."""
import asyncio
import redis.asyncio as aioredis
from backend.auth._core import get_settings


async def clear_rate_limits():
    """Clear all rate limit entries from Redis."""
    settings = get_settings()

    # Connect to Redis
    redis_client = aioredis.from_url(settings.REDIS_URL)

    try:
        # Get all rate limit keys (they follow pattern: rl:*)
        pattern = "rl:*"
        cursor = 0
        keys_deleted = 0

        while True:
            cursor, keys = await redis_client.scan(cursor, match=pattern)
            if keys:
                keys_deleted += await redis_client.delete(*keys)

            if cursor == 0:
                break

        print(f"[OK] Cleared {keys_deleted} rate limit entries from Redis")
        return keys_deleted

    finally:
        await redis_client.aclose()


if __name__ == "__main__":
    asyncio.run(clear_rate_limits())
