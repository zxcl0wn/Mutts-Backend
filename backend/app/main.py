from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from .core.dependencies import get_user_service
from .database import init_db
from .auth.routes import auth_router
from .routes import game_router, matchmaking_router
from .core.redis import get_redis
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
        while True:
            try:
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
