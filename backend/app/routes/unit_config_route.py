from fastapi import APIRouter, Depends, Request
from ..core.rate_limiter import limiter
from ..repositories import UnitRepository
from ..core.dependencies import get_unit_repository
from pydantic import BaseModel


router = APIRouter()


class UnitConfigResponse(BaseModel):
    name: str
    hp: int
    attack: int
    attack_speed: float
    attack_range: int
    attack_type: str
    crit_chance: float
    crit_damage: float
    move_speed: float
    cost: int


class GameConfigResponse(BaseModel):
    initial_hp: int
    initial_coins: int
    new_round_coins: int
    max_units_on_board: int
    max_units_on_bench: int
    sell_refund_percent: float
    planning_time: int
    board_size_x: int
    board_size_y: int


@router.get("/unit-configs")
@limiter.limit("20/minute")
async def get_unit_configs(request: Request, unit_repo: UnitRepository = Depends(get_unit_repository)) -> list[UnitConfigResponse]:
    configs = await unit_repo.get_all()
    return [
        UnitConfigResponse(
            name=config.name,
            hp=config.hp,
            attack=config.attack,
            attack_speed=config.attack_speed,
            attack_range=config.attack_range,
            attack_type=config.attack_type.value,
            crit_chance=config.crit_chance,
            crit_damage=config.crit_damage,
            move_speed=config.move_speed,
            cost=config.mana_cost,
        )
        for config in configs
    ]


@router.get("/game-config")
@limiter.limit("20/minute")
async def get_game_config(request: Request) -> GameConfigResponse:
    from .. import game_constants
    return GameConfigResponse(
        initial_hp=game_constants.INITIAL_HP,
        initial_coins=game_constants.INITIAL_COINS,
        new_round_coins=game_constants.NEW_ROUND_COINS,
        max_units_on_board=game_constants.MAX_UNITS_ON_BOARD,
        max_units_on_bench=game_constants.MAX_UNITS_ON_BENCH,
        sell_refund_percent=game_constants.SELL_REFUND_PERCENT,
        planning_time=game_constants.PLANNING_TIME,
        board_size_x=game_constants.BOARD_SIZE_X,
        board_size_y=game_constants.BOARD_SIZE_Y,
    )
