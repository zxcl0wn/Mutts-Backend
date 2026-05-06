from pydantic import BaseModel
from .player_schema import PlayerState
from .unit_schema import Unit
from .. import game_constants


class GameState(BaseModel):
    game_id: str
    player1: PlayerState
    player2: PlayerState
    units: list[Unit] = []
    phase: str = game_constants.GamePhases.PLANNING.value
    round: int = 1
    timer: int = game_constants.PLANNING_TIME
    status: str = game_constants.GameStatus.WAITING.value
    winner: str|None = None

    class Config:
        from_attributes = True
