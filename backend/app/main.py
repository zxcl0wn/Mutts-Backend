from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager

from sqlalchemy.util import await_only

from .core.dependencies import get_user_service
from .database import init_db
from .auth.routes import auth_router
from .routes import game_router, matchmaking_router
from .core.redis import get_redis
import asyncio
from .repositories import PlayerRepository, GameRepository
from .services.matchmaking_service import MatchmakingService
from .services import UserService


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    asyncio.create_task(matchmaking_background_task())
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(game_router)
app.include_router(matchmaking_router)



@app.get("/")
def test() -> dict[str, str]:
    return {
        "status": "OK"
    }


@app.get('/leaderboard')
async def leaderboard(
        user_service: UserService = Depends(get_user_service)
):
    all_players = await user_service.get_best_users_by_rating()
    return {
        "players": all_players
    }


async def matchmaking_background_task():
    """Фоновая задача для автоматического создания матчей"""
    print("🔄 Matchmaking background task started")
    
    # Создаем подключение к Redis перед циклом
    redis = await get_redis()
    
    try:
        heartbeat = 0
        while True:
            try:
                await asyncio.sleep(1)
                heartbeat += 1
                if heartbeat % 5 == 0:
                    qsize = await redis.scard("matchmaking_queue")
                    print(f"[heartbeat] queue={qsize}")
                
                # Получаем сервисы
                player_repo = PlayerRepository(redis)
                game_repo = GameRepository(redis)
                matchmaking_service = MatchmakingService(player_repo, game_repo)

                # Ищем пару игроков
                match = await matchmaking_service.find_match()

                if match:
                    player1, player2 = match
                    game_id = await matchmaking_service.create_game_for_players(player1, player2)
                    print(f"✓ Game created: {game_id} for {player1} vs {player2}")
                
            except Exception as e:
                import traceback
                print(f"❌ Matchmaking error: {e}")
                traceback.print_exc()
                await asyncio.sleep(5)
    finally:
        # Закрываем подключение при завершении задачи
        await redis.aclose()
        print("🔄 Matchmaking background task stopped")
