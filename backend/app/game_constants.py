from enum import Enum

class GamePhases(Enum):
    PLANNING = "planning"
    BATTLE = "battle"


class GameStatus(Enum):
    WAITING = "waiting"
    ACTIVE = "active"
    ENDED = "ended"


class UnitLocation(Enum):
    BOARD = "board"
    BENCH = "bench"


# Время
PLANNING_TIME = 20

NEW_ROUND_COINS = 5
INITIAL_COINS = 10  # Начальные монеты
INITIAL_HP = 100    # Начальное HP

# Лимиты юнитов
MAX_UNITS_ON_BOARD = 6
MAX_UNITS_ON_BENCH = 4
MAX_UNITS_TOTAL = 10  # На поле + на скамейке

# Размер поля (общая доска)
BOARD_SIZE_X = 7  # Ширина
BOARD_SIZE_Y = 8  # Длина (7x8 = 56 клеток)

# Половины поля для каждого игрока
PLAYER1_Y_RANGE = (0, 3)  # Player 1: y от 0 до 3 (7x4 = 28 клеток)
PLAYER2_Y_RANGE = (4, 7)  # Player 2: y от 4 до 7 (7x4 = 28 клеток)

# Игровые правила
SELL_REFUND_PERCENT = 0,5
