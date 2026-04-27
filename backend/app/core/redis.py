from redis.asyncio import Redis
from ..config import get_settings


settings = get_settings()

async def get_redis() -> Redis:
    return Redis.from_url(settings.redis.url)
