from ..repositories import PlayerRepository, GameRepository
from ..schemas import GameState, PlayerState
import uuid
from .. import game_constants


class MatchmakingService:
    def __init__(self, player_repo: PlayerRepository, game_repo: GameRepository) -> None:
        self.player_repo = player_repo
        self.game_repo = game_repo


    async def join_queue(self, username: str) -> dict:
        """Добавить игрока в очередь поиска игры"""
        # Проверяем что игрок не в активной игре
        game_id = await self.player_repo.get_player_game(username)
        if game_id:
            return {
                "success": False,
                "error": "Already in game"
            }

        # Добавляем в очередь
        success = await self.player_repo.add_to_queue(username)
        if not success:
            return {
                "success": False,
                "error": "Already in queue"
            }
        
        # Получаем размер очереди
        queue_size = await self.player_repo.get_queue_size()
        return {
            "success": True,
            "status": "searching",
            "queue_size": queue_size
        }


    async def leave_queue(self, username: str) -> dict:
        """Выйти из очереди поиска"""
        await self.player_repo.remove_from_queue(username)
        return {
            "success": True,
            "status": "cancelled"
        }


    async def get_queue_status(self, username: str) -> dict:
        """Проверить статус в очереди"""
        # Проверяем в игре ли игрок
        game_id = await self.player_repo.get_player_game(username)
        if game_id:
            return {
                "status": "in_game",
                "game_id": game_id
            }
        
        # Проверяем в очереди ли игрок
        in_queue = await self.player_repo.is_in_queue(username)
        if in_queue:
            queue_size = await self.player_repo.get_queue_size()
            return {
                "status": "searching",
                "queue_size": queue_size
            }
        
        # Игрок не в игре и не в очереди
        return {
            "status": "idle"
        }


    async def find_match(self) -> tuple[str, str]|None:
        """Найти пару игроков из очереди"""
        queue_size = await self.player_repo.get_queue_size()
        if queue_size < 2:
            return None
        
        # Берем двух игроков из очереди
        players = await self.player_repo.pop_players(2)
        
        if len(players) == 2:
            return players[0], players[1]
        
        return None


    async def create_game_for_players(self, player1: str, player2: str) -> str:
        """Создать игру для двух игроков"""
        # Генерируем ID игры
        game_id = str(uuid.uuid4())
        
        # Создаем начальное состояние игры
        game_state = GameState(
            game_id=game_id,
            player1=PlayerState(
                username=player1,
                hp=game_constants.INITIAL_HP,
                coins=game_constants.INITIAL_COINS,
                max_units=game_constants.MAX_UNITS_TOTAL
            ),
            player2=PlayerState(
                username=player2,
                hp=game_constants.INITIAL_HP,
                coins=game_constants.INITIAL_COINS,
                max_units=game_constants.MAX_UNITS_TOTAL
            ),
            units=[],
            phase=game_constants.GamePhases.PLANNING.value,
            round=0,
            timer=0,
            status=game_constants.GameStatus.WAITING.value,
            winner=None
        )
        
        # Сохраняем игру в Redis
        await self.game_repo.create_game(game_state)
        
        # Привязываем игроков к игре
        await self.player_repo.assign_game(player1, game_id)
        await self.player_repo.assign_game(player2, game_id)
        
        # Уведомляем игроков о найденной игре
        await self.player_repo.publish_to_player(player1, {
            "type": "match_found",
            "game_id": game_id,
            "opponent": player2
        })
        
        await self.player_repo.publish_to_player(player2, {
            "type": "match_found",
            "game_id": game_id,
            "opponent": player1
        })
        
        return game_id
