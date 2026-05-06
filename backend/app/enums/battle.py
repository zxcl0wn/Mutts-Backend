from enum import Enum


class UnitState(str, Enum):
    """Состояния юнита в бою"""
    MOVING = "moving"
    ATTACKING = "attacking"


class BattleEventType(str, Enum):
    """Типы событий боя"""
    BATTLE_START = "battle_start"
    MOVEMENT = "movement"
    ATTACK = "attack"
    DEATH = "death"
    BATTLE_END = "battle_end"
