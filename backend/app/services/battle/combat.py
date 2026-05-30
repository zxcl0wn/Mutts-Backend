import random
from ...schemas import Unit, BattleEvent


class CombatSystem:
    """Система боя (атаки, урон)"""
    
    def can_attack(self, attacker: Unit, current_time: float) -> bool:
        """Проверить может ли юнит атаковать (прошло ли достаточно времени)"""
        return current_time - attacker.last_attack_time >= attacker.attack_speed


    def attack(self, attacker: Unit, target: Unit, current_time: float) -> tuple[BattleEvent, int]:
        """
        Выполнить атаку.
        Возвращает событие атаки и урон
        """
        # Рассчитываем урон
        damage = self.calculate_damage(attacker)

        # Запоминаем время атаки
        attacker.last_attack_time = current_time
        
        # Возвращаем событие и урон
        event = BattleEvent(
            time=current_time,
            type="attack",
            unit_id=attacker.id,
            target_id=target.id,
            damage=damage,
            crit=(damage > attacker.attack),
            position=(attacker.position_x, attacker.position_y)
        )
        
        return event, damage
    

    def apply_damage(self, target: Unit, damage: int) -> None:
        """Применить урон к цели"""
        target.hp -= damage


    def calculate_damage(self, attacker: Unit) -> int:
        """Рассчитать урон (с учетом критического удара)"""
        damage = attacker.attack
        
        # Проверяем крит
        if random.random() < attacker.crit_chance:
            damage = int(damage * attacker.crit_damage)
        
        return damage


    def check_death(self, unit: Unit, current_time: float) -> BattleEvent|None:
        """
        Проверить смерть юнита.
        Возвращает событие смерти или None
        """
        if unit.hp <= 0 and not unit._death_recorded:
            unit._death_recorded = True
            return BattleEvent(
                time=current_time,
                type="death",
                unit_id=unit.id,
                position=(unit.position_x, unit.position_y)
            )
        return None
