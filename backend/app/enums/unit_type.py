from enum import Enum


class UnitType(str, Enum):
    """Типы юнитов"""

    ARCHITECT = "ARCHITECT"
    BARRICADE = "BARRICADE"
    BERSERKER = "BERSERKER"
    BULLDOZER = "BULLDOZER"
    CATAPULT = "CATAPULT"
    DRONE = "DRONE"
    GUNNER = "GUNNER"
    MEDIC = "MEDIC"
    PHANTOM = "PHANTOM"
    SCRAMBLER = "SCRAMBLER"
    SNIPER = "SNIPER"
    TECHNICIAN = "TECHNICIAN"
    TURRET = "TURRET"
