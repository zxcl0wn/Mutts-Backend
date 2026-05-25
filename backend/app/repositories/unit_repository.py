from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models import UnitConfig


class UnitRepository:
    """Репозиторий для работы с конфигурациями юнитов"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    
    async def get_by_type(self, unit_type: str) -> UnitConfig|None:
        """Получить конфигурацию юнита по типу"""
        result = await self.db.execute(
            select(UnitConfig).where(UnitConfig.name == unit_type)
        )
        return result.scalar_one_or_none()


    async def get_all(self) -> list[UnitConfig]:
        """Получить все конфигурации юнитов"""
        result = await self.db.execute(select(UnitConfig))
        return result.scalars().all()


    async def get_by_id(self, unit_id: int) -> UnitConfig|None:
        """Получить конфигурацию юнита по ID"""
        result = await self.db.execute(
            select(UnitConfig).where(UnitConfig.id == unit_id)
        )
        return result.scalar_one_or_none()
