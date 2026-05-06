import math
from ...schemas.unit_schema import Unit
from ...schemas.battle import BattleEvent


class Pathfinding:
    """Система движения юнитов"""
    
    def move_to_target(self, unit: Unit, target: Unit, delta_time: float, current_time: float) -> BattleEvent | None:
        """
        Двигать юнита к цели (плавное движение)
        
        Возвращает событие движения или None
        """
        dx = target.position_x - unit.position_x
        dy = target.position_y - unit.position_y
        
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance < 0.01:
            # Уже на месте
            return None
        
        # Нормализуем направление
        dx_norm = dx / distance
        dy_norm = dy / distance
        
        # Двигаемся
        move_distance = unit.move_speed * delta_time
        unit.position_x += dx_norm * move_distance
        unit.position_y += dy_norm * move_distance
        
        # Возвращаем событие движения
        return BattleEvent(
            time=current_time,
            type="movement",
            unit_id=unit.id,
            position=(unit.position_x, unit.position_y)
        )
    
    def move_to_grid(self, unit: Unit, grid_x: int, grid_y: int, delta_time: float, current_time: float) -> BattleEvent | None:
        """
        Двигать юнита к центру клетки
        """
        target_x = float(grid_x) + 0.5  # Центр клетки
        target_y = float(grid_y) + 0.5  # Центр клетки
        
        dx = target_x - unit.position_x
        dy = target_y - unit.position_y
        
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance < 0.01:
            # Почти на месте - выравниваем точно
            unit.position_x = target_x
            unit.position_y = target_y
            return None
        
        # Нормализуем
        dx_norm = dx / distance
        dy_norm = dy / distance
        
        # Двигаемся (но не дальше чем до цели)
        move_distance = min(unit.move_speed * delta_time, distance)
        unit.position_x += dx_norm * move_distance
        unit.position_y += dy_norm * move_distance
        
        return BattleEvent(
            time=current_time,
            type="movement",
            unit_id=unit.id,
            position=(unit.position_x, unit.position_y)
        )
    
    def calculate_distance(self, unit1: Unit, unit2: Unit) -> float:
        """Евклидово расстояние между юнитами"""
        dx = unit2.position_x - unit1.position_x
        dy = unit2.position_y - unit1.position_y
        return math.sqrt(dx**2 + dy**2)
    
    def calculate_grid_distance(self, unit1: Unit, unit2: Unit) -> int:
        """Чебышевское расстояние (по клеткам)"""
        grid_x1 = math.floor(unit1.position_x)
        grid_y1 = math.floor(unit1.position_y)
        grid_x2 = math.floor(unit2.position_x)
        grid_y2 = math.floor(unit2.position_y)
        
        dx = abs(grid_x2 - grid_x1)
        dy = abs(grid_y2 - grid_y1)
        
        return max(dx, dy)
    
    def is_on_grid(self, unit: Unit) -> bool:
        """Проверить стоит ли юнит в центре клетки"""
        grid_x = math.floor(unit.position_x)
        grid_y = math.floor(unit.position_y)
        
        center_x = grid_x + 0.5
        center_y = grid_y + 0.5
        
        # Проверяем с небольшой погрешностью
        return abs(unit.position_x - center_x) < 0.01 and abs(unit.position_y - center_y) < 0.01
    
    def snap_to_grid(self, unit: Unit):
        """Выровнять юнита на центр ближайшей клетки"""
        grid_x = math.floor(unit.position_x)
        grid_y = math.floor(unit.position_y)
        
        unit.position_x = float(grid_x) + 0.5
        unit.position_y = float(grid_y) + 0.5
