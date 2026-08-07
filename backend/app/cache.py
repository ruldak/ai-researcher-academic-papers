import redis.asyncio as redis

from app.config import settings

# Initialize async Redis client using URL from environment variables.
redis_client = redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)

async def get_cache() -> redis.Redis:
    """
    Dependency to provide the async Redis client.
    """
    return redis_client