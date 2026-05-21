from .base import BaseRedisRepository
from ..schemas import GameState, PlayerState, Unit
import json


class GameRepository(BaseRedisRepository):
    async def create_game(self, game_state: GameState) -> str:
        """Создать новую игру"""
        key = f"game:{game_state.game_id}"

        data = {
            "game_id": game_state.game_id,
            "player1": game_state.player1.model_dump_json(),
            "player2": game_state.player2.model_dump_json(),
            "units": json.dumps([u.model_dump() for u in game_state.units]),
            "phase": game_state.phase,
            "round": game_state.round,
            "timer": game_state.timer,
            "status": game_state.status,
            "winner": game_state.winner
        }

        await self._set_hash(key, data, expire=3600)
        return game_state.game_id


    async def get_game(self, game_id: str) -> GameState|None:
        """Получить игру по ID"""
        key = f"game:{game_id}"
        data = await self._get_hash(key)

        if not data:
            return None

        return GameState(
            game_id=data["game_id"],
            player1=PlayerState.model_validate_json(data["player1"]),
            player2=PlayerState.model_validate_json(data["player2"]),
            units=[Unit(**unit) for unit in json.loads(data["units"])],
            phase=data["phase"],
            round=int(data["round"]),
            timer=int(data["timer"]),
            status=data["status"],
            winner=data.get("winner")
        )


    async def update_game(self, game_state: GameState):
        """Обновить состояние игры"""
        await self.create_game(game_state)


    async def delete_game(self, game_id: str):
        """Удалить игру"""
        await self._delete(f"game:{game_id}")


    async def add_connected_player(self, game_id: str, username: str):
        """Отметить игрока как подключенного"""
        await self.redis.sadd(f"game:{game_id}:connected", username)


    async def remove_connected_player(self, game_id: str, username: str):
        """Удалить игрока из списка подключенных"""
        await self.redis.srem(f"game:{game_id}:connected", username)


    async def get_connected_count(self, game_id: str) -> int:
        """Получить количество подключенных игроков"""
        return await self.redis.scard(f"game:{game_id}:connected")


    async def publish_to_game(self, game_id: str, message: dict):
        """Отправить сообщение в канал игры"""
        await self.redis.publish(
            f"game:{game_id}",
            json.dumps(message)
        )
