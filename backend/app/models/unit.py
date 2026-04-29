from pydantic import BaseModel
from .. import game_constants


class Unit(BaseModel):
    id: str
    type: str
    level: int = 1
    hp: int
    max_hp: int
    attack: int
    attack_speed: float
    range: int
    move_speed: float
    position_x: int
    position_y: int
    owner: str
    target_id: str|None = None  # ID цели для атаки
    location: str = game_constants.UnitLocation.BOARD

    class Config:
        from_attributes = True
