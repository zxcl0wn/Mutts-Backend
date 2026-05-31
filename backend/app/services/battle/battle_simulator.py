from ...schemas import GameState, Unit, BattleResult, BattleEvent
from ...repositories import UnitRepository
from .game_ai import GameAI
from .combat import CombatSystem
import math


# Константы симуляции
STEP_DURATION = 0.1  # 100ms на шаг
MAX_STEPS = 3000  # Максимум 300 секунд боя  # TODO: endless fight


class BattleSimulator:
    """Главный класс симуляции боя"""
    
    def __init__(self, unit_repository: UnitRepository) -> None:
        self.unit_repo = unit_repository
        self.game_ai = GameAI()
        self.combat = CombatSystem()


    async def simulate(self, game: GameState) -> BattleResult:
        """
        Главный метод симуляции боя;
        Возвращает BattleResult с событиями и победителем
        """
        # Инициализируем бой
        player1_units, player2_units = self._initialize_battle(game)
        
        # Запускаем главный цикл боя
        events, winner = self._run_battle_loop(player1_units, player2_units)
        
        # Подсчитываем живых
        player1_alive = sum(1 for u in player1_units if u.hp > 0)
        player2_alive = sum(1 for u in player2_units if u.hp > 0)
        
        # Длительность боя
        duration = events[-1].time if events else 0.0
        
        return BattleResult(
            events=events,
            winner=winner,
            player1_alive=player1_alive,
            player2_alive=player2_alive,
            duration=duration
        )


    def _initialize_battle(self, game: GameState) -> tuple[list[Unit], list[Unit]]:
        """Подготовить юнитов к бою"""
        import copy
        
        # Фильтруем только юнитов на поле
        all_units = [unit for unit in game.units if unit.location == "board"]
        
        # Создаем копии юнитов для симуляции
        battle_units = [copy.deepcopy(unit) for unit in all_units]
        
        # Восстанавливаем HP всех юнитов перед боем
        for unit in battle_units:
            unit.hp = unit.max_hp
        
        # Инициализируем боевые параметры
        for unit in battle_units:
            # Устанавливаем last_attack_time в отрицательное значение чтобы юнит мог атаковать сразу
            unit.last_attack_time = -unit.attack_speed
            unit.target_id = None
            unit._death_recorded = False
        
        # Разделяем по игрокам
        player1_units = [unit for unit in battle_units if unit.owner == game.player1.username]
        player2_units = [unit for unit in battle_units if unit.owner == game.player2.username]

        return player1_units, player2_units


    def _run_battle_loop(self, player1_units: list[Unit], player2_units: list[Unit]) -> tuple[list[BattleEvent], str]:
        """Главный цикл боя"""
        events = []
        current_time = 0.0
        step = 0
        
        # Событие начала боя
        events.append(BattleEvent(
            time=current_time,
            type="battle_start"
        ))
        print(f"\n{'='*80}")
        print(f"🎬 BATTLE STARTED")
        print(f"   Player 1: {len(player1_units)} units")
        print(f"   Player 2: {len(player2_units)} units")
        print(f"{'='*80}")
        
        # Выводим начальное состояние (TICK 0)
        print(f"\n--- TICK 0 (t=0.0s) | P1: {len(player1_units)} alive | P2: {len(player2_units)} alive ---")
        for unit in player1_units:
            print(f"   [{unit.owner}] {unit.type} (lvl {unit.level}, id={unit.id[:8]}) | HP: {unit.hp}/{unit.max_hp} | Pos: ({unit.position_x:.1f}, {unit.position_y:.1f}) | OnGrid: {self.game_ai.pathfinding.is_on_grid(unit)}")
        for unit in player2_units:
            print(f"   [{unit.owner}] {unit.type} (lvl {unit.level}, id={unit.id[:8]}) | HP: {unit.hp}/{unit.max_hp} | Pos: ({unit.position_x:.1f}, {unit.position_y:.1f}) | OnGrid: {self.game_ai.pathfinding.is_on_grid(unit)}")
        print()
        
        while step < MAX_STEPS:
            step += 1
            current_time = round(step * STEP_DURATION, 1)
            
            # Считаем живых до обновления
            p1_alive = sum(1 for unit in player1_units if unit.hp > 0)
            p2_alive = sum(1 for unit in player2_units if unit.hp > 0)
            
            # Проверяем окончание боя
            if self._check_battle_end(player1_units, player2_units):
                print(f"\n⏹️  BATTLE ENDED at step {step} (t={current_time:.1f}s)")
                break
            
            # Выводим заголовок тика
            print(f"\n--- TICK {step} (t={current_time:.1f}s) | P1: {p1_alive} alive | P2: {p2_alive} alive ---")
            
            # Собираем занятые клетки на текущий тик
            all_units = player1_units + player2_units
            occupied_cells: set[tuple[int, int]] = set()
            for unit in all_units:
                if unit.hp > 0:
                    gx = math.floor(unit.position_x)
                    gy = math.floor(unit.position_y)
                    occupied_cells.add((gx, gy))

            # Клетки к которым юниты уже движутся — тоже заняты
            for cell in self.game_ai._target_cells.values():
                occupied_cells.add(cell)

            # Собираем все атаки которые произойдут в этом тике
            pending_damage = []
            
            # Обновляем юнитов Player 1
            for unit in player1_units:
                if unit.hp <= 0:
                    continue

                events_before = len(events)
                attack_result = self.game_ai.update_unit(unit, player2_units, STEP_DURATION, current_time, events, obstacles=occupied_cells)
                
                # Если была атака, сохраняем урон для применения позже
                if attack_result:
                    target, damage = attack_result
                    print(f"   🔥 ATTACK: {unit.type} attack={unit.attack} → damage={damage} target HP before={target.hp}")
                    pending_damage.append((target, damage))
                
                # Выводим что делает юнит
                self._log_unit_action(unit, player2_units, events[events_before:], current_time)
            
            # Обновляем юнитов Player 2
            for unit in player2_units:
                if unit.hp <= 0:
                    continue

                events_before = len(events)
                attack_result = self.game_ai.update_unit(unit, player1_units, STEP_DURATION, current_time, events, obstacles=occupied_cells)
                
                # Если была атака, сохраняем урон для применения позже
                if attack_result:
                    target, damage = attack_result
                    print(f"   🔥 ATTACK: {unit.type} attack={unit.attack} → damage={damage} target HP before={target.hp}")
                    pending_damage.append((target, damage))
                
                # Выводим что делает юнит
                self._log_unit_action(unit, player1_units, events[events_before:], current_time)
            
            # Применяем весь урон одновременно
            for target, damage in pending_damage:
                old_hp = target.hp
                self.combat.apply_damage(target, damage)
                print(f"   💥 APPLY DMG: {damage} to {target.type} → HP {old_hp} → {target.hp}")
            
            # Проверяем смерти
            all_units = player1_units + player2_units
            for unit in all_units:
                death_event = self.combat.check_death(unit, current_time)
                if death_event:
                    events.append(death_event)
                    print(f"   💀 {unit.type} (lvl {unit.level}, id={unit.id[:8]}) DIED | Owner: {unit.owner} | HP: {unit.hp}")
        
        # Событие конца боя
        events.append(BattleEvent(
            time=current_time,
            type="battle_end"
        ))
        
        # Итоговая статистика
        p1_alive = sum(1 for unit in player1_units if unit.hp > 0)
        p2_alive = sum(1 for unit in player2_units if unit.hp > 0)
        winner = self._determine_winner(player1_units, player2_units)
        
        print(f"\n{'='*80}")
        print(f"🏁 BATTLE FINISHED at t={current_time:.1f}s")
        print(f"   Winner: {winner}")
        print(f"   Player 1: {p1_alive} alive")
        print(f"   Player 2: {p2_alive} alive")
        
        # Рассчитываем урон
        if winner == "player1":
            damage_to_p2 = p1_alive + 1
            damage_to_p1 = 0
        elif winner == "player2":
            damage_to_p1 = p2_alive + 1
            damage_to_p2 = 0
        else:
            damage_to_p1 = 1
            damage_to_p2 = 1
        
        print(f"   Damage to Player 1: {damage_to_p1}")
        print(f"   Damage to Player 2: {damage_to_p2}")
        print(f"{'='*80}\n")
        
        return events, winner


    def _log_unit_action(self, unit: Unit, enemies: list[Unit], new_events: list[BattleEvent], current_time: float) -> None:
        """Вывести действие юнита в консоль"""
        # Находим цель
        target = None
        if unit.target_id:
            for enemy in enemies:
                if enemy.id == unit.target_id:
                    target = enemy
                    break
        
        # Определяем действие
        action = "IDLE"
        details = ""
        
        # Всегда показываем OnGrid
        is_on_grid = self.game_ai.pathfinding.is_on_grid(unit)
        
        if not target:
            action = "SEARCHING"
            details = f"no target | Pos: ({unit.position_x:.1f}, {unit.position_y:.1f}) | OnGrid: {is_on_grid}"
        else:
            # Вычисляем расстояние до цели
            grid_dist = self.game_ai.pathfinding.calculate_grid_distance(unit, target)
            
            # Проверяем что произошло
            attacked = False
            moved = False
            damage = 0
            crit = False
            
            for event in new_events:
                if event.type == "attack" and event.unit_id == unit.id:
                    attacked = True
                    damage = event.damage
                    crit = event.crit
                    action = "ATTACKING"
                elif event.type == "movement" and event.unit_id == unit.id:
                    moved = True
            
            if attacked:
                crit_mark = " 💥CRIT" if crit else ""
                details = f"→ {target.type} (id={target.id[:8]}) | DMG: {damage}{crit_mark} | Dist: {grid_dist} | Pos: ({unit.position_x:.1f}, {unit.position_y:.1f}) | Target HP: {target.hp}/{target.max_hp} | OnGrid: {is_on_grid}"
                action = "ATTACKING"
            elif moved:
                action = "MOVING"
                details = f"→ {target.type} (id={target.id[:8]}) | Dist: {grid_dist} | Pos: ({unit.position_x:.1f}, {unit.position_y:.1f}) | OnGrid: {is_on_grid}"
            else:
                # Стоит и ждет attack_speed
                time_since_attack = current_time - unit.last_attack_time
                action = "WAITING"
                details = f"cooldown {time_since_attack:.1f}/{unit.attack_speed}s | Dist: {grid_dist} | Pos: ({unit.position_x:.1f}, {unit.position_y:.1f}) | OnGrid: {is_on_grid}"
        
        print(f"   [{unit.owner}] {unit.type} (lvl {unit.level}, id={unit.id[:8]}) | HP: {unit.hp}/{unit.max_hp} | {action} {details}")

    
    def _check_battle_end(self, player1_units: list[Unit], player2_units: list[Unit]) -> bool:
        """Проверка окончания боя"""
        player1_alive = sum(1 for units in player1_units if units.hp > 0)
        player2_alive = sum(1 for units in player2_units if units.hp > 0)
        
        # Бой заканчивается когда хотя бы у одного из игроков все юниты мертвы
        return player1_alive == 0 or player2_alive == 0


    def _determine_winner(self, player1_units: list[Unit], player2_units: list[Unit]) -> str:
        """Определить победителя"""
        player1_alive = sum(1 for units in player1_units if units.hp > 0)
        player2_alive = sum(1 for units in player2_units if units.hp > 0)
        
        if player1_alive > 0 and player2_alive == 0:
            return "player1"
        elif player2_alive > 0 and player1_alive == 0:
            return "player2"
        else:
            return "draw"
