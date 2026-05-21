from pydantic import BaseModel
from typing import Literal


class BattleEvent(BaseModel):
    """Событие боя для replay"""
    time: float
    type: Literal["battle_start", "movement", "attack", "death", "battle_end"]
    unit_id: str|None = None
    target_id: str|None = None
    damage: int|None = None
    crit: bool|None = None
    position: tuple[float, float]|None = None


class BattleResult(BaseModel):
    """Результат симуляции боя"""
    events: list[BattleEvent]
    winner: Literal["player1", "player2", "draw"]
    player1_alive: int
    player2_alive: int
    duration: float
