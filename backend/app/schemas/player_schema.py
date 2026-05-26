from pydantic import BaseModel


class PlayerState(BaseModel):
    username: str
    hp: int = 100
    coins: float = 10
    max_units: int = 10

    class Config:
        from_attributes = True
