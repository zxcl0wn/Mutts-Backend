from enum import Enum

class UnitType(str, Enum):
    """Типы юнитов"""
    WARRIOR = "warrior"
    ARCHER = "archer"
    MAGE = "mage"
    
    # Добавляй новых юнитов здесь:
    # TANK = "tank"
    # ASSASSIN = "assassin"
