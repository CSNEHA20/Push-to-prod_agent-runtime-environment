import os
from typing import Optional
import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

redis_client: Optional[aioredis.Redis] = None


async def init_redis() -> aioredis.Redis:
    """Initialize async Redis client."""
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return redis_client


async def get_redis() -> aioredis.Redis:
    """Dependency / getter for async Redis client instance."""
    if redis_client is None:
        return await init_redis()
    return redis_client


async def close_redis() -> None:
    """Close async Redis connection."""
    global redis_client
    if redis_client is not None:
        await redis_client.close()
        redis_client = None
