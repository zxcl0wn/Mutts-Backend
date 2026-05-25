from ...schemas import Unit, BattleEvent
from .combat import CombatSystem
from .pathfinding import Pathfinding


class GameAI:
    """AI юнитов (FSM)"""
    
    def __init__(self):
        self.combat = CombatSystem()
        self.pathfinding = Pathfinding()
        self._target_cells: dict[str, tuple[int, int]] = {}  # unit_id -> (gx, gy) куда движется


    def update_unit(self, unit: Unit, enemies: list[Unit], delta_time: float,
                    current_time: float, events: list[BattleEvent],
                    obstacles: set[tuple[int, int]] | None = None) -> tuple[Unit, int]|None:
        """
        Обновить состояние юнита.
        Возвращает если произошла атака, иначе None
        """
        # Пропускаем мертвых
        if unit.hp <= 0:
            return None
        
        # Проверяем жива ли цель
        if unit.target_id:
            target = self._find_unit_by_id(unit.target_id, enemies)
            if not target or target.hp <= 0:
                # Цель умерла - сбрасываем
                unit.target_id = None

        # Ищем цель если нет
        if not unit.target_id:
            target = self.find_nearest_enemy(unit, enemies)
            if target:
                unit.target_id = target.id
            else:
                # Нет врагов
                return None
        
        # Получаем текущую цель
        target = self._find_unit_by_id(unit.target_id, enemies)
        if not target:
            return None
        
        import math
        grid_distance = self.pathfinding.calculate_grid_distance(unit, target)

        if grid_distance <= unit.range:
            # В радиусе атаки
            self._target_cells.pop(unit.id, None)

            if self.pathfinding.is_on_grid(unit):
                if self.combat.can_attack(unit, current_time):
                    event, damage = self.combat.attack(unit, target, current_time)
                    events.append(event)
                    return (target, damage)
            else:
                cell_x = math.floor(unit.position_x)
                cell_y = math.floor(unit.position_y)
                event = self.pathfinding.move_to_grid(unit, cell_x, cell_y, delta_time, current_time)
                if event:
                    events.append(event)
        else:
            # Вне радиуса — движение по сетке
            if self.pathfinding.is_on_grid(unit):
                # Дошли до центра — выбираем следующую клетку
                my_cell_x = math.floor(unit.position_x)
                my_cell_y = math.floor(unit.position_y)
                target_cell_x = math.floor(target.position_x)
                target_cell_y = math.floor(target.position_y)

                # Клетка цели не препятствие (чтобы могли подойти вплотную)
                target_in_obstacles = False
                if obstacles is not None:
                    target_in_obstacles = (target_cell_x, target_cell_y) in obstacles
                    obstacles.discard((target_cell_x, target_cell_y))

                next_cell = self.pathfinding.get_next_cell(my_cell_x, my_cell_y, target_cell_x, target_cell_y, obstacles=obstacles)
                if next_cell:
                    self._target_cells[unit.id] = next_cell
                    if obstacles is not None:
                        obstacles.add(next_cell)  # резервируем для этого тика
                    cell_x, cell_y = next_cell
                    event = self.pathfinding.move_to_grid(unit, cell_x, cell_y, delta_time, current_time)
                    if event:
                        events.append(event)

                # Восстанавливаем target_cell если он был в obstacles
                if obstacles is not None and target_in_obstacles:
                    obstacles.add((target_cell_x, target_cell_y))
            else:
                # Идём к сохранённой клетке — тоже резервируем
                if unit.id in self._target_cells:
                    cell_x, cell_y = self._target_cells[unit.id]
                    if obstacles is not None:
                        obstacles.add((cell_x, cell_y))
                    event = self.pathfinding.move_to_grid(unit, cell_x, cell_y, delta_time, current_time)
                    if event:
                        events.append(event)
                else:
                    cell_x = math.floor(unit.position_x)
                    cell_y = math.floor(unit.position_y)
                    event = self.pathfinding.move_to_grid(unit, cell_x, cell_y, delta_time, current_time)
                    if event:
                        events.append(event)
        
        return None

    
    def find_nearest_enemy(self, unit: Unit, enemies: list[Unit]) -> Unit|None:
        """Найти ближайшего живого врага"""
        nearest = None
        min_distance = float('inf')

        for enemy in enemies:
            if enemy.hp <= 0:
                continue
            
            distance = self.pathfinding.calculate_distance(unit, enemy)
            if distance < min_distance:
                min_distance = distance
                nearest = enemy
        
        return nearest


    def _find_unit_by_id(self, unit_id: str, units: list[Unit]) -> Unit|None:
        """Найти юнита по ID"""
        for unit in units:
            if unit.id == unit_id:
                return unit
        return None
