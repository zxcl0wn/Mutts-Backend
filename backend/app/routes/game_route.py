from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect
from redis import Redis
from ..auth.utils.auth_utils import verify_token
from ..core.dependencies import get_game_service, get_game_repository
from ..services import GameService
from ..repositories import GameRepository
from fastapi import HTTPException, status
from ..core.redis import get_redis
from ..core.timer_manager import timer_manager
import json
import asyncio


router = APIRouter(
    prefix="/ws/game"
)


@router.websocket("/{game_id}")
async def game_websocket(
        websocket: WebSocket,
        game_id: str,
        access_token: str,
        game_service: GameService = Depends(get_game_service),
        game_repo: GameRepository = Depends(get_game_repository),
        redis: Redis = Depends(get_redis)
):
    username = None
    try:
        # 1. Валидация
        username = await verify_token(access_token)
        await game_service.check_player_in_game(username, game_id)

        # 2. Принимаем соединение
        await websocket.accept()
        print(f"✓ {username} connected to game {game_id}")

        # 3. Регистрируем игрока как подключенного
        await game_repo.add_connected_player(game_id, username)

        # 4. Отправляем начальное состояние игры
        game = await game_repo.get_game(game_id)
        if game:
            await websocket.send_json({
                "type": "game_state",
                "state": game.model_dump()
            })

        # 5. Проверяем все ли игроки подключились
        connected_count = await game_repo.get_connected_count(game_id)
        if connected_count == 2:
            # Все подключились - можно стартовать игру
            await game_repo.publish_to_game(game_id, {
                "type": "all_players_connected"
            })
            

            await asyncio.sleep(1)
            await game_repo.publish_to_game(game_id, {
                "type": "countdown",
                "value": 3
            })
            await asyncio.sleep(1)
            await game_repo.publish_to_game(game_id, {
                "type": "countdown",
                "value": 2
            })
            await asyncio.sleep(1)
            await game_repo.publish_to_game(game_id, {
                "type": "countdown",
                "value": 1
            })
            await asyncio.sleep(1)
            
            # Запускаем фазу планирования
            await game_service.start_planning_phase(game_id)
            
            # Запускаем таймер
            await timer_manager.start_planning_timer(game_id, game_service, game_repo)

        # 6. Подписываемся на Pub/Sub
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"game:{game_id}")

        # 7. listener для Pub/Sub в отдельной задаче
        async def listen_redis():
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    data_str = message['data'].decode('utf-8') if isinstance(message['data'], bytes) else message['data']
                    await websocket.send_text(data_str)

        listener_task = asyncio.create_task(listen_redis())

        # 8. Основной цикл приема сообщений от клиента
        try:
            while True:
                data = await websocket.receive_json()

                # Обработка разных типов сообщений
                if data["type"] == "place_unit":
                    result = await game_service.place_unit(
                        game_id, username,
                        data["unit_type"]
                    )
                    # GameService сделал publish_to_game, все получат уведомление

                elif data["type"] == "move_unit":
                    result = await game_service.move_unit(
                        game_id, username,
                        data["unit_id"], data["x"], data["y"], data["location"]
                    )

                elif data["type"] == "sell_unit":
                    result = await game_service.sell_unit(
                        game_id, username,
                        data["unit_id"]
                    )

                # TODO: Добавить другие типы сообщений (merge_units, ready, и т.д.)

        except WebSocketDisconnect:
            print(f"✗ {username} disconnected from game {game_id}")

        finally:
            # Очистка при отключении
            listener_task.cancel()
            await pubsub.unsubscribe(f"game:{game_id}")
            if username:
                await game_repo.remove_connected_player(game_id, username)
                # TODO: Обработать отключение игрока (пауза игры, автопроигрыш и т.д.)

    except HTTPException as e:
        await websocket.close(code=e.status_code, reason=e.detail)
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=str(e))