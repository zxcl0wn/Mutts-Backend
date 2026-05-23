import asyncio
from typing import Dict
from ..repositories import GameRepository
from ..services import GameService
from .. import game_constants


class TimerManager:
    """Управление таймерами для игр"""

    def __init__(self):
        self.active_timers: Dict[str, asyncio.Task] = {}

    
    async def start_planning_timer(
        self, 
        game_id: str, 
        game_service: GameService,
        game_repo: GameRepository,
        duration: int = None
    ):
        """Запустить таймер фазы планирования"""
        if duration is None:
            duration = game_constants.PLANNING_TIME
        
        # Отменяем предыдущий таймер если есть
        await self.cancel_timer(game_id)
        
        # Создаем новую задачу
        task = asyncio.create_task(
            self._planning_timer_task(game_id, duration, game_service, game_repo)
        )
        self.active_timers[game_id] = task
        print(f"⏱️  Planning timer started for game {game_id}: {duration} seconds")
    
    
    async def _planning_timer_task(
        self,
        game_id: str,
        duration: int,
        game_service: GameService,
        game_repo: GameRepository
    ):
        """Задача таймера планирования"""
        try:
            # Обратный отсчет
            for remaining in range(duration, 0, -1):
                # Broadcast обновление таймера
                await game_repo.publish_to_game(game_id, {
                    "type": "timer_update",
                    "time_left": remaining
                })
                
                await asyncio.sleep(1)
            
            # Таймер закончился
            print(f"⏱️  Planning timer ended for game {game_id}")
            
            # Автоматически запускаем фазу боя
            await game_service.start_battle_phase(game_id)
            
            # Удаляем таймер из активных
            if game_id in self.active_timers:
                del self.active_timers[game_id]
        
        except asyncio.CancelledError:
            print(f"⏱️  Planning timer cancelled for game {game_id}")
            raise
        except Exception as e:
            print(f"❌ Timer error for game {game_id}: {e}")
    
    
    async def cancel_timer(self, game_id: str):
        """Отменить таймер игры"""
        if game_id in self.active_timers:
            task = self.active_timers[game_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.active_timers[game_id]
            print(f"⏱️  Timer cancelled for game {game_id}")
    

# Глобальный экземпляр
timer_manager = TimerManager()
