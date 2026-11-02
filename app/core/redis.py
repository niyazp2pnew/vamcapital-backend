import redis.asyncio as aioredis
from app.core.config import settings

# Shared async Redis client pool
redis_client = aioredis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)


async def get_redis():
    """FastAPI Dependency for route-level Redis injection."""
    return redis_client