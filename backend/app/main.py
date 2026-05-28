from fastapi import FastAPI, Depends, Request
from contextlib import asynccontextmanager
from .core.dependencies import get_user_service
from .database import init_db
from .auth.routes import auth_router
from .routes import game_router, matchmaking_router, unit_config_router
from .core.redis import get_redis
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from .core.rate_limiter import limiter
import asyncio
from .repositories import PlayerRepository, GameRepository
from .services import MatchmakingService, UserService
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    asyncio.create_task(matchmaking_background_task())
    yield


app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins = [
    "http://194.87.35.96",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


app.include_router(auth_router)
app.include_router(game_router)
app.include_router(matchmaking_router)
app.include_router(unit_config_router)



@app.get("/")
def test() -> dict[str, str]:
    return {
        "status": "OK!!"
    }


@app.get('/leaderboard')
@limiter.limit("20/minute")
async def leaderboard(
        request: Request,
        user_service: UserService = Depends(get_user_service)
):
    all_players = await user_service.get_best_users_by_rating()
    return {
        "players": all_players
    }


_matchmaking_alive = False


@app.get("/debug/matchmaking")
async def debug_matchmaking():
    redis = await get_redis()
    try:
        queue = await redis.smembers("matchmaking_queue")
        queue_players = [p.decode() for p in queue]
        return {
            "task_alive": _matchmaking_alive,
            "queue": queue_players,
            "queue_size": len(queue_players)
        }
    finally:
        await redis.aclose()


async def matchmaking_background_task():
    """Фоновая задача для автоматического создания матчей"""
    global _matchmaking_alive
    print("🔄 Matchmaking background task started")

    redis = None

    try:
        while True:
            try:
                if redis is None:
                    redis = await get_redis()

                _matchmaking_alive = True
                player_repo = PlayerRepository(redis)
                game_repo = GameRepository(redis)
                matchmaking_service = MatchmakingService(player_repo, game_repo)

                match = await matchmaking_service.find_match()

                if match:
                    player1, player2 = match
                    game_id = await matchmaking_service.create_game_for_players(player1, player2)
                    print(f"✓ Game created: {game_id} for {player1} vs {player2}")
                else:
                    await asyncio.sleep(1)

            except Exception as e:
                import traceback
                print(f"❌ Matchmaking error: {e}")
                traceback.print_exc()
                if redis is not None:
                    try:
                        await redis.aclose()
                    except:
                        pass
                    redis = None
                await asyncio.sleep(5)
    finally:
        _matchmaking_alive = False
        if redis is not None:
            await redis.aclose()
        print("🔄 Matchmaking background task stopped")
