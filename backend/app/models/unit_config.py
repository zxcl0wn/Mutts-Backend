from sqlalchemy import Column, Integer, String, Float, Text, Enum as SQLEnum
from ..database import Base
import enum


class AttackType(enum.Enum):
    MELEE = "melee"
    RANGED = "ranged"


class UnitConfig(Base):
    __tablename__ = "unit_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)

    hp = Column(Integer, nullable=False)
    attack = Column(Integer, nullable=False)

    attack_speed = Column(Float, nullable=False)
    attack_range = Column(Integer, nullable=False)
    attack_type = Column(SQLEnum(AttackType), nullable=False)
    # projectile_speed = Column(Float, nullable=True)

    crit_chance = Column(Float, nullable=False, default=0.0)
    crit_damage = Column(Float, nullable=False, default=2.0)

    move_speed = Column(Float, nullable=False)

    mana_cost = Column(Integer, nullable=False)

    # role = Column(String(20), nullable=False)
    # passive_ability = Column(String(50), nullable=True)

    def __repr__(self):
        return f"<UnitConfig(id={self.id}, name='{self.name}')>"
