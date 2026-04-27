from pydantic import BaseModel


class Unit(BaseModel):
    id: str  # Уникальный ID юнита
    type: str  # "archer", "warrior", "mage" и тд
    level: int = 1  # Уровень после слияния
    hp: int
    max_hp: int
    attack: int
    attack_speed: float  # Атак в секунду
    range: int  # Дальность атаки
    move_speed: float
    position_x: int
    position_y: int
    owner: str  # username владельца
    target_id: str|None = None  # ID цели для атаки

    class Config:
        from_attributes = True
