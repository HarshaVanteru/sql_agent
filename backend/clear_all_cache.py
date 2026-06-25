"""Clear all cache from Redis, including rate limits."""
import asyncio
import redis.asyncio as aioredis
from signup._core import get_settings


async def clear_all_cache():
    """Clear all cache entries from Redis."""
    settings = get_settings()

    # Connect to Redis
    redis_client = aioredis.from_url(settings.REDIS_URL)

    try:
        # Get all keys
        all_keys = await redis_client.keys("*")

        if all_keys:
            print(f"Found {len(all_keys)} keys in Redis:")
            for key in all_keys:
                print(f"  - {key}")

            # Delete all keys
            deleted = await redis_client.delete(*all_keys)
            print(f"\n[OK] Cleared {deleted} cache entries from Redis")
        else:
            print("[OK] No keys found in Redis - cache is already clean")

    finally:
        await redis_client.aclose()


if __name__ == "__main__":
    asyncio.run(clear_all_cache())
