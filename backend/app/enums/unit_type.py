from enum import Enum

class UnitType(str, Enum):
    """Типы юнитов"""
    WARRIOR = "warrior"
    ARCHER = "archer"
    MAGE = "mage"
