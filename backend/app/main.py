from fastapi import FastAPI
from contextlib import asynccontextmanager
from .database import init_db
from .auth.routes import auth_router
from .routes import game_router, matchmaking_router
from .core.redis import get_redis
from .core.dependencies import get_matchmaking_service
import asyncio


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


async def matchmaking_background_task():
    """Фоновая задача для автоматического создания матчей"""
    print("🔄 Matchmaking background task started")
    
    # Создаем подключение к Redis ОДИН РАЗ перед циклом
    redis = await get_redis()
    
    try:
        while True:
            try:
                await asyncio.sleep(1)
                
                # Получаем сервисы (используем одно и то же подключение)
                from .repositories import PlayerRepository, GameRepository
                player_repo = PlayerRepository(redis)
                game_repo = GameRepository(redis)
                from .services.matchmaking_service import MatchmakingService
                matchmaking_service = MatchmakingService(player_repo, game_repo)

                # Ищем пару игроков
                match = await matchmaking_service.find_match()

                if match:
                    player1, player2 = match
                    game_id = await matchmaking_service.create_game_for_players(player1, player2)
                    print(f"✓ Game created: {game_id} for {player1} vs {player2}")
                
            except Exception as e:
                print(f"❌ Matchmaking error: {e}")
                await asyncio.sleep(5)
    finally:
        # Закрываем подключение при завершении задачи
        await redis.aclose()
        print("🔄 Matchmaking background task stopped")
