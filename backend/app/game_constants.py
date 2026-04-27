from enum import Enum

class GamePhases(Enum):
    PLANNING = "planning"
    BATTLE = "battle"


class GameStatus(Enum):
    WAITING = "waiting"
    ACTIVE = "active"
    ENDED = "ended"


PLANNING_TIME=20
NEW_ROUND_COINS=5