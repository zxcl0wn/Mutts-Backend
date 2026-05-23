from ..repositories import GameRepository, PlayerRepository, UnitRepository, UserRepository
from ..schemas import Unit
import uuid
from fastapi import HTTPException, status
from .. import game_constants
from ..enums import UnitType
from ..database import AsyncSessionLocal
import random


class GameService:
    def __init__(self, game_repository: GameRepository, player_repository: PlayerRepository, unit_repository: UnitRepository) -> None:
        self.game_repo = game_repository
        self.player_repo = player_repository
        self.unit_repo = unit_repository


    async def place_unit(self, game_id: str, username: str, unit_type: UnitType) -> dict:
        """Разместить юнита (автоматически на поле или скамейку)"""
        game = await self.game_repo.get_game(game_id)
        if not game or game.phase != game_constants.GamePhases.PLANNING.value:
            return {
                "success": False,
                "error": "Invalid game state"
            }

        # Определяем игрока
        if game.player1.username == username:
            player = game.player1
        else:
            player = game.player2

        # Проверяем монеты
        unit_cost = await self._get_unit_cost(unit_type)
        if player.coins < unit_cost:
            return {
                "success": False,
                "error": "Not enough coins"
            }

        # Считаем юнитов игрока
        player_units = [unit for unit in game.units if unit.owner == username]
        if len(player_units) >= game_constants.MAX_UNITS_TOTAL:
            return {
                "success": False,
                "error": "Max units reached"
            }

        # Количество юнитов
        units_on_board = [unit for unit in player_units if unit.location == "board"]
        units_on_bench = [unit for unit in player_units if unit.location == "bench"]

        # Определяем куда разместить юнита
        if len(units_on_board) < game_constants.MAX_UNITS_ON_BOARD:
            # Есть место на поле → случайная пустая клетка на своей половине
            occupied_positions = {(unit.position_x, unit.position_y) for unit in units_on_board}
            
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
                return {
                    "success": False,
                    "error": "No space on board"
                }
            
            x, y = random.choice(empty_positions)
            location = "board"
        else:
            # Поле заполнено → скамейка
            if len(units_on_bench) >= game_constants.MAX_UNITS_ON_BENCH:
                return {
                    "success": False,
                    "error": "No space available"
                }
            
            # Находим первый свободный слот на скамейке
            occupied_slots = {u.position_x for u in units_on_bench}
            free_slot = next(i for i in range(game_constants.MAX_UNITS_ON_BENCH) if i not in occupied_slots)
            x, y = free_slot, 0
            location = "bench"

        # Создаем юнита
        unit = await self._create_unit(unit_type, username, x, y, location)
        game.units.append(unit)

        # Списываем монеты
        player.coins -= unit_cost

        # Проверяем автоматический мердж
        merged_unit = await self._check_auto_merge(game, username, unit)
        
        # Сохраняем
        await self.game_repo.update_game(game)

        # Уведомляем игроков - всегда отправляем unit_placed
        await self.game_repo.publish_to_game(game_id, {
            "type": "unit_placed",
            "unit": unit.model_dump(),
            "player": username,
            "coins_left": player.coins
        })

        # Если произошел автомердж - отправляем дополнительно auto_merge
        if merged_unit:
            await self.game_repo.publish_to_game(game_id, {
                "type": "auto_merge",
                "merged_unit": merged_unit.model_dump(),
                "player": username,
                "coins_left": player.coins
            })
            return {
                "success": True,
                "unit_id": merged_unit.id,
                "merged": True
            }
        else:
            return {
                "success": True,
                "unit_id": unit.id,
                "location": location,
                "position_x": x,
                "position_y": y
            }


    async def _get_unit_cost(self, unit_type: UnitType) -> int:
        """Получить стоимость юнита из БД"""
        unit_config = await self.unit_repo.get_by_type(unit_type)
        if not unit_config:
            return 3  # Дефолтная стоимость
        return unit_config.mana_cost


    async def _create_unit(self, unit_type: UnitType, owner: str, x: int, y: int, location: str = "board") -> Unit:
        """Создать юнита с характеристиками из БД"""
        unit_config = await self.unit_repo.get_by_type(unit_type)
        
        if not unit_config:
            raise ValueError(f"Unit type '{unit_type.value}' not found in database")
        
        return Unit(
            id=str(uuid.uuid4()),
            type=unit_type.value,
            level=1,
            hp=unit_config.hp,
            max_hp=unit_config.hp,
            attack=unit_config.attack,
            attack_speed=unit_config.attack_speed,
            range=int(unit_config.attack_range),
            move_speed=unit_config.move_speed,
            position_x=float(x) + 0.5,
            position_y=float(y) + 0.5,
            owner=owner,
            location=location,
            crit_chance=unit_config.crit_chance,
            crit_damage=unit_config.crit_damage
        )


    async def _check_auto_merge(self, game, username: str, new_unit: Unit) -> Unit|None:
        """Проверить и выполнить автоматический мердж если возможно"""
        # Ищем юнитов того же типа и уровня
        matching_units = [
            unit for unit in game.units
            if unit.owner == username
            and unit.type == new_unit.type
            and unit.level == new_unit.level
            and unit.id != new_unit.id  # Исключаем только что созданного юнита
        ]
        
        # Нужно минимум 2 одинаковых юнита для автомерджа
        if len(matching_units) >= 1:
            # Проверяем максимальный уровень
            if new_unit.level >= 4:
                return None  # Уже максимальный уровень
            
            # Берем первого для слияния с новым
            unit1 = matching_units[0]
            
            # Получаем конфигурацию юнита из БД
            unit_type = UnitType(new_unit.type)
            unit_config = await self.unit_repo.get_by_type(unit_type)
            
            if not unit_config:
                return None
            
            # Создаем нового юнита следующего уровня
            new_level = new_unit.level+1
            
            # Увеличиваем характеристики (формула: base * 2^(level-1))
            multiplier = 2 ** (new_level - 1)
            new_hp = int(unit_config.hp * multiplier)
            new_attack = int(unit_config.attack * multiplier)
            
            # Создаем улучшенного юнита на позиции первого
            merged_unit = Unit(
                id=str(uuid.uuid4()),
                type=new_unit.type,
                level=new_level,
                hp=new_hp,
                max_hp=new_hp,
                attack=new_attack,
                attack_speed=unit_config.attack_speed,
                range=int(unit_config.attack_range),
                move_speed=unit_config.move_speed,
                position_x=unit1.position_x,
                position_y=unit1.position_y,
                owner=username,
                location=unit1.location,
                crit_chance=unit_config.crit_chance,
                crit_damage=unit_config.crit_damage
            )
            
            # Удаляем два старых юнита
            game.units = [unit for unit in game.units if unit.id not in [new_unit.id, unit1.id]]
            
            # Добавляем нового
            game.units.append(merged_unit)
            
            # Рекурсивно проверяем еще раз (может быть цепочка мерджей)
            next_merge = await self._check_auto_merge(game, username, merged_unit)
            return next_merge if next_merge else merged_unit
        
        return None


    async def check_player_in_game(self, username: str, game_id: str) -> None:
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
            return {
                "success": False,
                "error": "Invalid game state"
            }

        # Находим юнита
        unit = None
        for u in game.units:
            if u.id == unit_id:
                unit = u
                break

        if not unit:
            return {
                "success": False,
                "error": "Unit not found"
            }

        # Проверяем что юнит принадлежит игроку
        if unit.owner != username:
            return {
                "success": False,
                "error": "Not your unit"
            }

        # Валидация в зависимости от location
        if location == "board":
            # Перемещение на поле
            if x < 0 or x >= game_constants.BOARD_SIZE_X:
                return {
                    "success": False,
                    "error": "Invalid board position"
                }
            
            # Определяем диапазон Y для игрока
            if game.player1.username == username:
                y_min, y_max = game_constants.PLAYER1_Y_RANGE
            else:
                y_min, y_max = game_constants.PLAYER2_Y_RANGE
            
            # Проверяем что Y в диапазоне своей половины
            if y < y_min or y > y_max:
                return {
                    "success": False,
                    "error": "Cannot place unit on opponent's side"
                }
            
            # Проверяем что клетка не занята
            player_units = [
                unit for unit in game.units
                if unit.owner == username
                   and unit.location == "board"
                   and unit.id != unit_id
            ]
            if any(unit.position_x == x and unit.position_y == y for unit in player_units):
                return {
                    "success": False,
                    "error": "Position occupied"
                }
            
            # Проверяем лимит юнитов на поле (если перемещаем со скамейки)
            if unit.location == "bench":
                units_on_board = [
                    unit for unit in player_units
                    if unit.location == "board"
                ]
                if len(units_on_board) >= game_constants.MAX_UNITS_ON_BOARD:
                    return {
                        "success": False,
                        "error": "Board is full"
                    }
        
        elif location == "bench":
            # Перемещение на скамейку
            if x < 0 or x >= game_constants.MAX_UNITS_ON_BENCH:
                return {
                    "success": False,
                    "error": "Invalid bench slot"
                }
            
            # Проверяем что слот не занят
            player_units = [
                unit for unit in game.units
                if unit.owner == username
                and unit.location == "bench"
                and unit.id != unit_id
            ]
            if any(unit.position_x == x for unit in player_units):
                return {
                    "success": False,
                    "error": "Bench slot occupied"
                }
            y = 0  # На скамейке y всегда 0
        
        else:
            return {
                "success": False,
                "error": "Invalid location"
            }

        # Обновляем позицию и location
        unit.position_x, unit.position_y, unit.location = x, y, location

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

        return {
            "success": True
        }


    async def sell_unit(self, game_id: str, username: str, unit_id: str) -> dict:
        """Продать юнита и вернуть часть монет"""
        game = await self.game_repo.get_game(game_id)
        if not game or game.phase != game_constants.GamePhases.PLANNING.value:
            return {
                "success": False,
                "error": "Invalid game state"
            }

        # Находим юнита
        unit, unit_index = None, None
        for i, u in enumerate(game.units):
            if u.id == unit_id:
                unit = u
                unit_index = i
                break

        if not unit:
            return {
                "success": False,
                "error": "Unit not found"
            }

        # Проверяем что юнит принадлежит игроку
        if unit.owner != username:
            return {
                "success": False,
                "error": "Not your unit"
            }

        # Определяем игрока
        if game.player1.username == username:
            player = game.player1
        else:
            player = game.player2

        # Возвращаем % стоимости юнита
        unit_cost = await self._get_unit_cost(UnitType(unit.type))
        refund = unit_cost * game_constants.SELL_REFUND_PERCENT
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

        return {
            "success": True,
            "refund": refund,
            "coins_left": player.coins
        }


    async def start_planning_phase(self, game_id: str, start_timer: bool = False) -> dict:
        """Начать фазу планирования (новый раунд)"""
        game = await self.game_repo.get_game(game_id)
        if not game:
            return {
                "success": False,
                "error": "Game not found"
            }

        # Увеличиваем раунд
        game.round += 1
        game.phase = game_constants.GamePhases.PLANNING.value
        game.timer = game_constants.PLANNING_TIME

        # Начисляем монеты игрокам за новый раунд  # TODO: дополнительное начисление монет за бонусы
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
        
        # Запускаем таймер если нужно
        if start_timer:
            from ..core.timer_manager import timer_manager
            await timer_manager.start_planning_timer(game_id, self, self.game_repo)

        return {
            "success": True,
            "round": game.round
        }


    async def start_battle_phase(self, game_id: str) -> dict:
        """Начать фазу боя"""
        import asyncio
        from .battle.battle_simulator import BattleSimulator

        game = await self.game_repo.get_game(game_id)
        if not game:
            return {
                "success": False,
                "error": "Game not found"
            }

        if game.phase != game_constants.GamePhases.PLANNING.value:
            return {
                "success": False,
                "error": "Not in planning phase"
            }

        # Изменяем фазу на battle
        game.phase = game_constants.GamePhases.BATTLE.value
        # Сохраняем
        await self.game_repo.update_game(game)

        # Уведомляем игроков о начале боя
        await self.game_repo.publish_to_game(game_id, {
            "type": "battle_phase_start",
            "round": game.round
        })

        # Запускаем симуляцию боя
        print(f"⚔️  Battle phase started for game {game_id}, running simulation...")
        battle_simulator = BattleSimulator(self.unit_repo)
        battle_result = await battle_simulator.simulate(game)
        
        print(f"⚔️  Battle simulation completed:")
        print(f"   Winner: {battle_result.winner}")
        print(f"   Duration: {battle_result.duration:.1f}s")
        print(f"   Player1 alive: {battle_result.player1_alive}")
        print(f"   Player2 alive: {battle_result.player2_alive}")
        print(f"   Total events: {len(battle_result.events)}")
        
        # Выводим краткую статистику событий
        event_types = {}
        for event in battle_result.events:
            event_types[event.type] = event_types.get(event.type, 0) + 1
        print(f"   Events breakdown: {event_types}")
        
        # Восстанавливаем HP всех юнитов в game.units
        for unit in game.units:
            unit.hp = unit.max_hp
        print(f"   HP restored for all units in game state")
        
        # Отправляем события боя клиентам
        await self.game_repo.publish_to_game(game_id, {
            "type": "battle_events",
            "events": [event.model_dump() for event in battle_result.events]
        })

        # Анимация боя
        wait_time = battle_result.duration + 2.0
        print(f"   Waiting {wait_time:.1f}s for clients to replay battle...")
        await asyncio.sleep(wait_time)

        # Считаем живых юнитов на поле
        player1_alive, player2_alive  = battle_result.player1_alive, battle_result.player2_alive

        # Определяем победителя раунда и рассчитываем урон
        # Бой идет до конца - пока все юниты одной стороны не умрут
        damage_to_player1 = damage_to_player2 = 0
        
        if player1_alive > 0 and player2_alive == 0:
            # Player 1 победил раунд
            round_winner = game.player1.username
            damage_to_player2 = player1_alive + 1

        elif player2_alive > 0 and player1_alive == 0:
            # Player 2 победил раунд
            round_winner = game.player2.username
            damage_to_player1 = player2_alive + 1

        else:
            # Ничья раунда
            round_winner = "draw"
            damage_to_player1 = 1
            damage_to_player2 = 1
        
        # Наносим урон
        game.player1.hp -= damage_to_player1
        game.player2.hp -= damage_to_player2
        
        # Проверяем условие победы
        game_winner, game_ended = None, False
        
        if game.player1.hp <= 0 and game.player2.hp <= 0:
            # Ничья
            game_winner = "draw"
            game_ended = True
            game.status = game_constants.GameStatus.ENDED.value


        elif game.player1.hp <= 0:
            # Player 2 победил
            game_winner = game.player2.username
            game_ended = True
            game.status = game_constants.GameStatus.ENDED.value
            game.winner = game.player2.username

        elif game.player2.hp <= 0:
            # Player 1 победил
            game_winner = game.player1.username
            game_ended = True
            game.status = game_constants.GameStatus.ENDED.value
            game.winner = game.player1.username
        
        # Сохраняем изменения
        await self.game_repo.update_game(game)
        
        # Уведомляем о конце боя
        await self.game_repo.publish_to_game(game_id, {
            "type": "battle_phase_end",
            "round": game.round,
            "round_winner": round_winner,
            "damage_to_player1": damage_to_player1,
            "damage_to_player2": damage_to_player2,
            "player1_hp": game.player1.hp,
            "player2_hp": game.player2.hp
        })
        
        print(f"⚔️  Battle phase ended for game {game_id}")
        
        if game_ended:
            # Игра завершена
            await self.game_repo.publish_to_game(game_id, {
                "type": "game_over",
                "winner": game_winner,
                "player1_hp": game.player1.hp,
                "player2_hp": game.player2.hp
            })
            
            print(f"🏆 Game {game_id} ended. Winner: {game_winner}")

            # Обновляем рейтинг и счётчики
            try:
                async with AsyncSessionLocal() as db:
                    user_repo = UserRepository(db)
                    new_r1, new_r2 = await user_repo.update_match_stats(game.player1.username, game.player2.username, game_winner)
                    if new_r1 or new_r2:
                        print(f"   Stats updated: {game.player1.username}={new_r1}, {game.player2.username}={new_r2}")

            except Exception as e:
                print(f"   Stats update failed: {e}")

            # Освобождаем игроков (удаляем привязки к игре)
            await self.player_repo.remove_player_game(game.player1.username)
            await self.player_repo.remove_player_game(game.player2.username)
            print(f"   Players {game.player1.username} and {game.player2.username} are now free")
            
            # Удаляем игру из Redis через некоторое время (чтобы клиенты успели получить game_over)
            import asyncio
            async def cleanup_game():
                await asyncio.sleep(5)
                # Удаляем игру
                await self.game_repo.delete_game(game_id)
                
                # Удаляем список подключенных игроков
                await self.game_repo.redis.delete(f"game:{game_id}:connected")
                
                print(f"   Game {game_id} fully removed from Redis")
            
            # Запускаем cleanup в фоне
            asyncio.create_task(cleanup_game())
        else:
            # Игра продолжается - следующий раунд
            await self.start_planning_phase(game_id, start_timer=True)

        return {
            "success": True
        }
