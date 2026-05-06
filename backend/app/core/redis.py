from redis.asyncio import Redis
from ..config import settings


async def get_redis() -> Redis:
    return Redis.from_url(settings.redis.url)
