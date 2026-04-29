from fastapi import Depends
from ..core.redis import get_redis
from ..repositories import GameRepository, PlayerRepository
from ..services import GameService
from ..services.matchmaking_service import MatchmakingService
from redis.asyncio import Redis


async def get_game_repository(redis: Redis = Depends(get_redis)) -> GameRepository:
    return GameRepository(redis)


async def get_player_repository(redis: Redis = Depends(get_redis)) -> PlayerRepository:
    return PlayerRepository(redis)


async def get_game_service(
    game_repo: GameRepository = Depends(get_game_repository),
    player_repo: PlayerRepository = Depends(get_player_repository)
) -> GameService:
    return GameService(game_repo, player_repo)


async def get_matchmaking_service(
    player_repo: PlayerRepository = Depends(get_player_repository),
    game_repo: GameRepository = Depends(get_game_repository)
) -> MatchmakingService:
    return MatchmakingService(player_repo, game_repo)