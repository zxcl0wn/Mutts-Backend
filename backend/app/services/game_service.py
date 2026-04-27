from ..repositories import GameRepository, PlayerRepository
from ..models import Unit
import uuid
from fastapi import HTTPException, status
from .. import game_constants


class GameService:
    def __init__(self, game_repository: GameRepository, player_repository: PlayerRepository):
        self.game_repo = game_repository
        self.player_repo = player_repository


    async def place_unit(self, game_id: int, username: str, unit_type: str, x: int, y: int) -> dict:
        """Разместить юнита на поле"""
        game = await self.game_repo.get_game(game_id)

        if not game or game.phase != game_constants.GamePhases.PLANNING.value:
            return {"success": False, "error": "Invalid game state"}

        # Определяем игрока
        if game.player1.username == username:
            player = game.player1
        else:
            player = game.player2

        # Проверяем монеты
        unit_cost = self._get_unit_cost(unit_type)
        if player.coins < unit_cost:
            return {"success": False, "error": "Not enough coins"}

        # Проверяем лимит юнитов
        player_units = [unit for unit in game.units if unit.owner == username]
        if len(player_units) >= player.max_units:
            return {"success": False, "error": "Max units reached"}

        # Создаем юнита
        unit = self._create_unit(unit_type, username, x, y)
        game.units.append(unit)

        # Списываем монеты
        player.coins -= unit_cost

        # Сохраняем
        await self.game_repo.update_game(game)

        # # Уведомляем игроков
        # await self.game_repo.publish_to_game(game_id, {
        #     "type": "unit_placed",
        #     "unit": unit.model_dump(),
        #     "player": username,
        #     "coins_left": player.coins
        # })

        return {"success": True, "unit_id": unit.id}


    def _get_unit_cost(self, unit_type: str) -> int:
        """Получить стоимость юнита"""
        costs = {
            "warrior": 3,
            "archer": 4,
            "mage": 5
        }
        return costs.get(unit_type, 3)


    def _create_unit(self, unit_type: str, owner: str, x: int, y: int) -> Unit:
        """Создать юнита с базовыми характеристиками"""
        stats = {
            "warrior": {"hp": 100, "attack": 20, "range": 1, "attack_speed": 1.0, "move_speed": 2.0},
            "archer": {"hp": 60, "attack": 15, "range": 5, "attack_speed": 1.5, "move_speed": 2.5},
            "mage": {"hp": 50, "attack": 30, "range": 6, "attack_speed": 0.8, "move_speed": 2.0}
        }

        unit_stats = stats.get(unit_type, stats["warrior"])

        return Unit(
            id=str(uuid.uuid4()),
            type=unit_type,
            level=1,
            hp=unit_stats["hp"],
            max_hp=unit_stats["hp"],
            attack=unit_stats["attack"],
            attack_speed=unit_stats["attack_speed"],
            range=unit_stats["range"],
            move_speed=unit_stats["move_speed"],
            position_x=x,
            position_y=y,
            owner=owner
        )


    async def check_player_in_game(self, username: str, game_id: int):
        # Получаем игру из Redis
        game = await self.game_repo.get_game(game_id)

        if not game:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game not found"
            )

        # Проверяем, что игрок участвует в этой игре
        if username != game.player1.username and username != game.player2.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a player in this game"
            )

        # Проверяем статус игры
        if game.status == game_constants.GameStatus.ENDED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game has ended"
            )

    async def move_unit(self, game_id: int, username: str, unit_id: str, x: int, y: int) -> dict:
        """Переместить юнита на новую позицию"""
        game = await self.game_repo.get_game(game_id)

        if not game or game.phase != game_constants.GamePhases.PLANNING.value:
            return {"success": False, "error": "Invalid game state"}

        # Находим юнита
        unit = None
        for u in game.units:
            if u.id == unit_id:
                unit = u
                break

        if not unit:
            return {"success": False, "error": "Unit not found"}

        # Проверяем что юнит принадлежит игроку
        if unit.owner != username:
            return {"success": False, "error": "Not your unit"}

        # Проверяем что позиция валидна
        if x < 0 or y < 0:
            return {"success": False, "error": "Invalid position"}

        # Обновляем позицию
        unit.position_x = x
        unit.position_y = y

        # Сохраняем
        await self.game_repo.update_game(game)

        # Уведомляем игроков
        await self.game_repo.publish_to_game(game_id, {
            "type": "unit_moved",
            "unit_id": unit_id,
            "x": x,
            "y": y,
            "player": username
        })

        return {"success": True}


    async def sell_unit(self, game_id: int, username: str, unit_id: str) -> dict:
        """Продать юнита и вернуть часть монет"""
        game = await self.game_repo.get_game(game_id)

        if not game or game.phase != game_constants.GamePhases.PLANNING.value:
            return {"success": False, "error": "Invalid game state"}

        # Находим юнита
        unit = None
        unit_index = None
        for i, u in enumerate(game.units):
            if u.id == unit_id:
                unit = u
                unit_index = i
                break

        if not unit:
            return {"success": False, "error": "Unit not found"}

        # Проверяем что юнит принадлежит игроку
        if unit.owner != username:
            return {"success": False, "error": "Not your unit"}

        # Определяем игрока
        if game.player1.username == username:
            player = game.player1
        else:
            player = game.player2

        # Возвращаем 50% стоимости юнита
        unit_cost = self._get_unit_cost(unit.type)
        refund = unit_cost // 2
        player.coins += refund

        # Удаляем юнита
        game.units.pop(unit_index)
        
        # Сохраняем
        await self.game_repo.update_game(game)

        # Уведомляем игроков
        await self.game_repo.publish_to_game(game_id, {
            "type": "unit_sold",
            "unit_id": unit_id,
            "player": username,
            "refund": refund,
            "coins_left": player.coins
        })

        return {"success": True, "refund": refund, "coins_left": player.coins}


    async def start_planning_phase(self, game_id: int) -> dict:
        """Начать фазу планирования (новый раунд)"""
        game = await self.game_repo.get_game(game_id)

        if not game:
            return {"success": False, "error": "Game not found"}

        # Увеличиваем раунд
        game.round += 1
        game.phase = game_constants.GamePhases.PLANNING.value
        game.timer = game_constants.PLANNING_TIME

        # Начисляем монеты игрокам за новый раунд
        game.player1.coins += game_constants.NEW_ROUND_COINS
        game.player2.coins += game_constants.NEW_ROUND_COINS

        # Сохраняем
        await self.game_repo.update_game(game)

        # Уведомляем игроков
        await self.game_repo.publish_to_game(game_id, {
            "type": "planning_phase_start",
            "round": game.round,
            "time_left": game.timer,
            "player1_coins": game.player1.coins,
            "player2_coins": game.player2.coins
        })

        return {"success": True, "round": game.round}


    async def start_battle_phase(self, game_id: int) -> dict:
        """Начать фазу боя"""
        game = await self.game_repo.get_game(game_id)

        if not game:
            return {"success": False, "error": "Game not found"}

        if game.phase != game_constants.GamePhases.PLANNING.value:
            return {"success": False, "error": "Not in planning phase"}

        # Изменяем фазу на battle
        game.phase = game_constants.GamePhases.BATTLE.value

        # Сохраняем
        await self.game_repo.update_game(game)

        # Уведомляем игроков о начале боя
        await self.game_repo.publish_to_game(game_id, {
            "type": "battle_phase_start",
            "round": game.round
        })

        # TODO: Запустить BattleSimulator
        # battle_replay = await self.battle_simulator.simulate(game)
        # await self.game_repo.save_battle_replay(game_id, battle_replay)
        # await self.game_repo.publish_to_game(game_id, {
        #     "type": "battle_replay",
        #     "replay": battle_replay
        # })

        return {"success": True}