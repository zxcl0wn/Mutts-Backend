from .base import BaseRedisRepository
import json


class PlayerRepository(BaseRedisRepository):
    async def add_to_queue(self, username: str) -> bool:
        """Добавить игрока в очередь матчмейкинга"""
        # Проверяем, не в игре ли уже
        if await self.get_player_game(username):
            return False

        await self.redis.sadd("matchmaking_queue", username)
        return True


    async def remove_from_queue(self, username: str):
        """Убрать игрока из очереди"""
        await self.redis.srem("matchmaking_queue", username)


    async def get_queue_size(self) -> int:
        """Получить размер очереди"""
        return await self.redis.scard("matchmaking_queue")


    async def is_in_queue(self, username: str) -> bool:
        """Проверить находится ли игрок в очереди"""
        return await self.redis.sismember("matchmaking_queue", username)


    async def pop_players(self, count: int) -> list[str]:
        """Взять N игроков из очереди"""
        players = await self.redis.spop("matchmaking_queue", count)
        return [p.decode() for p in players] if players else []


    async def assign_game(self, username: str, game_id: str, expire: int = 3600):
        """Привязать игрока к игре"""
        await self.redis.setex(f"player:{username}:game_id", expire, game_id)


    async def get_player_game(self, username: str) -> str|None:
        """Получить ID игры игрока"""
        game_id = await self.redis.get(f"player:{username}:game_id")
        return game_id.decode() if game_id else None


    async def remove_player_game(self, username: str):
        """Удалить привязку игрока к игре"""
        await self.redis.delete(f"player:{username}:game_id")


    async def publish_to_player(self, username: str, message: dict):
        """Отправить сообщение игроку"""
        await self.redis.publish(
            f"player:{username}",
            json.dumps(message)
        )