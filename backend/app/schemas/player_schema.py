from pydantic import BaseModel
from typing import List


class PlayerState(BaseModel):
    username: str
    hp: int = 100
    coins: int = 10
    max_units: int = 10

    class Config:
        from_attributes = True
