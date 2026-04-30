from ..repositories import GameRepository, PlayerRepository
from ..models import Unit
import uuid
from fastapi import HTTPException, status
from .. import game_constants
import random


class GameService:
    def __init__(self, game_repository: GameRepository, player_repository: PlayerRepository):
        self.game_repo = game_repository
        self.player_repo = player_repository


    async def place_unit(self, game_id: str, username: str, unit_type: str) -> dict:
        """Разместить юнита"""
        game = await self.game_repo.get_game(game_id)

        if not game or game.phase != game_constants.GamePhases.PLANNING.value:
            return {"success": False, "error": "Invalid game state"}

        # Определяем игрока
        if game.player1.username == username:
            player = game.player1
        else:
            player = game.player2

        # Проверяем монеты
        unit_cost = game_constants.UNIT_COSTS.get(unit_type, 3)
        if player.coins < unit_cost:
            return {"success": False, "error": "Not enough coins"}

        # Считаем юнитов игрока
        player_units = [unit for unit in game.units if unit.owner == username]
        if len(player_units) >= game_constants.MAX_UNITS_TOTAL:
            return {"success": False, "error": "Max units reached"}

        # Количество юнитов
        units_on_board = [unit for unit in player_units if unit.location == "board"]
        units_on_bench = [unit for unit in player_units if unit.location == "bench"]

        # Определяем куда разместить юнита
        if len(units_on_board) < game_constants.MAX_UNITS_ON_BOARD:
            # Есть место на поле → случайная пустая клетка на своей половине
            occupied_positions = {(u.position_x, u.position_y) for u in units_on_board}
            
            # Определяем диапазон Y для игрока
            if game.player1.username == username:
                y_min, y_max = game_constants.PLAYER1_Y_RANGE
            else:
                y_min, y_max = game_constants.PLAYER2_Y_RANGE
            
            # Генерируем все позиции на своей половине поля
            all_positions = {(x, y) for x in range(game_constants.BOARD_SIZE_X) 
                           for y in range(y_min, y_max + 1)}
            empty_positions = list(all_positions - occupied_positions)
            
            if not empty_positions:
                return {"success": False, "error": "No space on board"}
            
            x, y = random.choice(empty_positions)
            location = "board"
        else:
            # Поле заполнено → скамейка
            if len(units_on_bench) >= game_constants.MAX_UNITS_ON_BENCH:
                return {"success": False, "error": "No space available"}
            
            # Находим первый свободный слот на скамейке
            occupied_slots = {u.position_x for u in units_on_bench}
            free_slot = next(i for i in range(game_constants.MAX_UNITS_ON_BENCH) if i not in occupied_slots)
            x, y = free_slot, 0
            location = "bench"

        # Создаем юнита
        unit = self._create_unit(unit_type, username, x, y, location)
        game.units.append(unit)

        # Списываем монеты
        player.coins -= unit_cost

        # Проверяем автоматический мердж
        merged_unit = await self._check_auto_merge(game, username, unit)
        
        # Сохраняем
        await self.game_repo.update_game(game)

        # Уведомляем игроков
        if merged_unit:
            # Произошел автомердж
            await self.game_repo.publish_to_game(game_id, {
                "type": "auto_merge",
                "merged_unit": merged_unit.model_dump(),
                "player": username,
                "coins_left": player.coins
            })
            return {"success": True, "unit_id": merged_unit.id, "merged": True}
        else:
            # Обычное размещение
            await self.game_repo.publish_to_game(game_id, {
                "type": "unit_placed",
                "unit": unit.model_dump(),
                "player": username,
                "coins_left": player.coins
            })
            return {"success": True, "unit_id": unit.id, "location": location, "position_x": x, "position_y": y}


    def _get_unit_cost(self, unit_type: str) -> int:
        """Получить стоимость юнита"""
        costs = {
            "warrior": 3,
            "archer": 4,
            "mage": 5
        }
        return costs.get(unit_type, 3)


    def _create_unit(self, unit_type: str, owner: str, x: int, y: int, location: str = "board") -> Unit:
        """Создать юнита с базовыми характеристиками"""
        unit_stats = game_constants.UNIT_STATS.get(unit_type, game_constants.UNIT_STATS["warrior"])

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
            owner=owner,
            location=location
        )


    async def _check_auto_merge(self, game, username: str, new_unit: Unit) -> Unit | None:
        """Проверить и выполнить автоматический мердж если возможно"""
        # Ищем юнитов того же типа и уровня
        matching_units = [
            u for u in game.units 
            if u.owner == username 
            and u.type == new_unit.type 
            and u.level == new_unit.level
            and u.id != new_unit.id  # Исключаем только что созданного юнита
        ]
        
        # Нужно минимум 2 одинаковых юнита для автомерджа (включая нового)
        if len(matching_units) >= 1:
            # Проверяем максимальный уровень
            if new_unit.level >= 4:
                return None  # Уже максимальный уровень
            
            # Берем первого для слияния с новым
            unit1 = matching_units[0]
            
            # Создаем нового юнита следующего уровня
            new_level = new_unit.level + 1
            base_stats = game_constants.UNIT_STATS.get(new_unit.type)
            
            # Увеличиваем характеристики (формула: base * 2^(level-1))
            multiplier = 2 ** (new_level - 1)
            new_hp = int(base_stats["hp"] * multiplier)
            new_attack = int(base_stats["attack"] * multiplier)
            
            # Создаем улучшенного юнита на позиции первого
            merged_unit = Unit(
                id=str(uuid.uuid4()),
                type=new_unit.type,
                level=new_level,
                hp=new_hp,
                max_hp=new_hp,
                attack=new_attack,
                attack_speed=base_stats["attack_speed"],
                range=base_stats["range"],
                move_speed=base_stats["move_speed"],
                position_x=unit1.position_x,
                position_y=unit1.position_y,
                owner=username,
                location=unit1.location
            )
            
            # Удаляем два старых юнита
            game.units = [u for u in game.units if u.id not in [new_unit.id, unit1.id]]
            
            # Добавляем нового
            game.units.append(merged_unit)
            
            # Рекурсивно проверяем еще раз (может быть цепочка мерджей)
            return await self._check_auto_merge(game, username, merged_unit)
        
        return None


    async def check_player_in_game(self, username: str, game_id: str):
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

    async def move_unit(self, game_id: str, username: str, unit_id: str, x: int, y: int, location: str) -> dict:
        """Переместить юнита"""
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

        # Валидация в зависимости от location
        if location == "board":
            # Перемещение на поле
            if x < 0 or x >= game_constants.BOARD_SIZE_X:
                return {"success": False, "error": "Invalid board position"}
            
            # Определяем диапазон Y для игрока
            if game.player1.username == username:
                y_min, y_max = game_constants.PLAYER1_Y_RANGE
            else:
                y_min, y_max = game_constants.PLAYER2_Y_RANGE
            
            # Проверяем что Y в диапазоне своей половины
            if y < y_min or y > y_max:
                return {"success": False, "error": "Cannot place unit on opponent's side"}
            
            # Проверяем что клетка не занята
            player_units = [u for u in game.units if u.owner == username and u.location == "board" and u.id != unit_id]
            if any(u.position_x == x and u.position_y == y for u in player_units):
                return {"success": False, "error": "Position occupied"}
            
            # Проверяем лимит юнитов на поле (если перемещаем со скамейки)
            if unit.location == "bench":
                units_on_board = [u for u in player_units if u.location == "board"]
                if len(units_on_board) >= game_constants.MAX_UNITS_ON_BOARD:
                    return {"success": False, "error": "Board is full"}
        
        elif location == "bench":
            # Перемещение на скамейку
            if x < 0 or x >= game_constants.MAX_UNITS_ON_BENCH:
                return {"success": False, "error": "Invalid bench slot"}
            
            # Проверяем что слот не занят
            player_units = [u for u in game.units if u.owner == username and u.location == "bench" and u.id != unit_id]
            if any(u.position_x == x for u in player_units):
                return {"success": False, "error": "Bench slot occupied"}
            
            y = 0  # На скамейке y всегда 0
        
        else:
            return {"success": False, "error": "Invalid location"}

        # Обновляем позицию и location
        unit.position_x = x
        unit.position_y = y
        unit.location = location

        # Сохраняем
        await self.game_repo.update_game(game)

        # Уведомляем игроков
        await self.game_repo.publish_to_game(game_id, {
            "type": "unit_moved",
            "unit_id": unit_id,
            "x": x,
            "y": y,
            "location": location,
            "player": username
        })

        return {"success": True}


    async def sell_unit(self, game_id: str, username: str, unit_id: str) -> dict:
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


    async def merge_units(self, game_id: str, username: str, unit_id_1: str, unit_id_2: str) -> dict:
        """Слить два юнита в один более высокого уровня"""
        game = await self.game_repo.get_game(game_id)

        if not game or game.phase != game_constants.GamePhases.PLANNING.value:
            return {"success": False, "error": "Invalid game state"}

        # Находим оба юнита
        unit1 = None
        unit2 = None
        unit1_index = None
        unit2_index = None
        
        for i, unit in enumerate(game.units):
            if unit.id == unit_id_1:
                unit1 = unit
                unit1_index = i
            if unit.id == unit_id_2:
                unit2 = unit
                unit2_index = i

        if not unit1 or not unit2:
            return {"success": False, "error": "One or both units not found"}

        # Проверяем что оба юнита принадлежат игроку
        if unit1.owner != username or unit2.owner != username:
            return {"success": False, "error": "Not your units"}

        # Проверяем что юниты одного типа
        if unit1.type != unit2.type:
            return {"success": False, "error": "Units must be of the same type"}

        # Проверяем что юниты одного уровня
        if unit1.level != unit2.level:
            return {"success": False, "error": "Units must be of the same level"}
        
        # Проверяем максимальный уровень
        if unit1.level >= 4:
            return {"success": False, "error": "Units are already at max level"}

        # Создаем нового юнита следующего уровня
        new_level = unit1.level + 1
        base_stats = game_constants.UNIT_STATS.get(unit1.type)
        
        # Увеличиваем характеристики
        multiplier = 2 ** (new_level - 1)
        new_hp = int(base_stats["hp"] * multiplier)
        new_attack = int(base_stats["attack"] * multiplier)
        
        # Берем позицию первого юнита
        new_unit = Unit(
            id=str(uuid.uuid4()),
            type=unit1.type,
            level=new_level,
            hp=new_hp,
            max_hp=new_hp,
            attack=new_attack,
            attack_speed=base_stats["attack_speed"],
            range=base_stats["range"],
            move_speed=base_stats["move_speed"],
            position_x=unit1.position_x,
            position_y=unit1.position_y,
            owner=username,
            location=unit1.location
        )

        # Удаляем старых юнитов
        if unit1_index > unit2_index:
            game.units.pop(unit1_index)
            game.units.pop(unit2_index)
        else:
            game.units.pop(unit2_index)
            game.units.pop(unit1_index)

        # Добавляем нового юнита
        game.units.append(new_unit)

        await self.game_repo.update_game(game)

        await self.game_repo.publish_to_game(game_id, {
            "type": "units_merged",
            "unit_id_1": unit_id_1,
            "unit_id_2": unit_id_2,
            "new_unit": new_unit.model_dump(),
            "player": username
        })
        
        return {"success": True, "new_unit": new_unit.model_dump()}


    async def start_planning_phase(self, game_id: str, start_timer: bool = False) -> dict:
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
            "time_left": game.timer
        })
        
        # Запускаем таймер если нужно (для следующих раундов)
        if start_timer:
            from ..core.timer_manager import timer_manager
            await timer_manager.start_planning_timer(game_id, self, self.game_repo)

        return {"success": True, "round": game.round}


    async def start_battle_phase(self, game_id: str) -> dict:
        """Начать фазу боя"""
        import asyncio
        
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
        # Пока заглушка - ждем 2 секунды
        print(f"⚔️  Battle phase started for game {game_id}, waiting 2 seconds...")
        await asyncio.sleep(2)
        
        # Уведомляем о конце боя
        await self.game_repo.publish_to_game(game_id, {
            "type": "battle_phase_end",
            "round": game.round,
            "winner": None  # Пока никто не побеждает
        })
        
        print(f"⚔️  Battle phase ended for game {game_id}")
        
        # Автоматически запускаем следующий раунд планирования с таймером
        await self.start_planning_phase(game_id, start_timer=True)

        return {"success": True}