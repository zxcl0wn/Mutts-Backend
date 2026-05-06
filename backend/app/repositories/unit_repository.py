from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.unit_config import UnitConfig
from ..enums.unit_type import UnitType
from typing import Optional


class UnitRepository:
    """Репозиторий для работы с конфигурациями юнитов"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_type(self, unit_type: UnitType) -> Optional[UnitConfig]:
        """Получить конфигурацию юнита по типу (name)"""
        result = await self.db.execute(
            select(UnitConfig).where(UnitConfig.name == unit_type.value)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self) -> list[UnitConfig]:
        """Получить все конфигурации юнитов"""
        result = await self.db.execute(select(UnitConfig))
        return result.scalars().all()
    
    async def get_by_id(self, unit_id: int) -> Optional[UnitConfig]:
        """Получить конфигурацию юнита по ID"""
        result = await self.db.execute(
            select(UnitConfig).where(UnitConfig.id == unit_id)
        )
        return result.scalar_one_or_none()
