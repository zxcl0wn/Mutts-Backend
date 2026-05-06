from pydantic import BaseModel
from .. import game_constants


class Unit(BaseModel):
    id: str
    type: str
    level: int = 1
    hp: int
    max_hp: int
    attack: int
    attack_speed: float  # Время между атаками в секундах
    range: int
    move_speed: float
    position_x: float
    position_y: float
    owner: str
    target_id: str | None = None
    location: str = game_constants.UnitLocation.BOARD.value

    last_attack_time: float = 0.0
    crit_chance: float = 0.0
    crit_damage: float = 1.5

    class Config:
        from_attributes = True
