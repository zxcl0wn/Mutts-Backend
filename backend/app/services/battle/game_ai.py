from ...schemas.unit_schema import Unit
from ...schemas.battle import BattleEvent
from ...enums.battle import UnitState
from .combat import CombatSystem
from .pathfinding import Pathfinding


class GameAI:
    """AI юнитов (FSM)"""
    
    def __init__(self):
        self.combat = CombatSystem()
        self.pathfinding = Pathfinding()


    def update_unit(self, unit: Unit, enemies: list[Unit], delta_time: float,
                    current_time: float, events: list[BattleEvent]) -> tuple[Unit, int]|None:
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
        
        # Проверяем расстояние до цели (по клеткам)
        grid_distance = self.pathfinding.calculate_grid_distance(unit, target)
        
        if grid_distance <= unit.range:
            # В радиусе атаки
            
            # Проверяем стоим ли ровно на клетке
            if self.pathfinding.is_on_grid(unit):
                # Стоим ровно на клетке - можем атаковать
                if self.combat.can_attack(unit, current_time):
                    # Атакуем (БЕЗ применения урона)
                    event, damage = self.combat.attack(unit, target, current_time)
                    events.append(event)
                    return (target, damage)  # Возвращаем цель и урон для применения позже
                else:
                    # Ждем attack_speed (стоим на месте)
                    pass
            else:
                # Не на клетке - выравниваемся на центр клетки
                import math
                grid_x = math.floor(unit.position_x)
                grid_y = math.floor(unit.position_y)
                event = self.pathfinding.move_to_grid(unit, grid_x, grid_y, delta_time, current_time)
                if event:
                    events.append(event)
        else:
            # Вне радиуса - двигаемся к цели
            event = self.pathfinding.move_to_target(unit, target, delta_time, current_time)
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
