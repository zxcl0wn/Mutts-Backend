from abc import ABC, abstractmethod
from redis.asyncio import Redis
from typing import Optional
import json


class BaseRedisRepository(ABC):
    def __init__(self, redis_client: Redis):
        self.redis = redis_client


    async def _set_hash(self, key: str, data: dict, expire: int = 60*60):
        """Сохранить hash в Redis"""
        serialized = {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                      for k, v in data.items()}
        await self.redis.hset(key, mapping=serialized)
        await self.redis.expire(key, expire)


    async def _get_hash(self, key: str) -> Optional[dict]:
        """Получить hash из Redis"""
        data = await self.redis.hgetall(key)
        if not data:
            return None
        return {k.decode(): v.decode() for k, v in data.items()}


    async def _delete(self, key: str):
        """Удалить ключ"""
        await self.redis.delete(key)
