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
BOARD_SIZE_X = 5  # Ширина
BOARD_SIZE_Y = 8  # Длина (5x8 = 40 клеток)

# Половины поля для каждого игрока
PLAYER1_Y_RANGE = (0, 3)  # Player 1: y от 0 до 3 (4 клетки)
PLAYER2_Y_RANGE = (4, 7)  # Player 2: y от 4 до 7 (4 клетки)

# Стоимость юнитов
UNIT_COSTS = {
    "warrior": 3,
    "archer": 4,
    "mage": 5
}

# Характеристики юнитов
UNIT_STATS = {
    "warrior": {"hp": 100, "attack": 20, "range": 1, "attack_speed": 1.0, "move_speed": 2.0},
    "archer": {"hp": 60, "attack": 15, "range": 5, "attack_speed": 1.5, "move_speed": 2.5},
    "mage": {"hp": 50, "attack": 30, "range": 6, "attack_speed": 0.8, "move_speed": 2.0}
}

# Игровые правила
SELL_REFUND_PERCENT = 50