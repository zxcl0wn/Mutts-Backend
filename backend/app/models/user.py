from sqlalchemy import Column, Integer, DateTime, String
from ..database import Base
import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    username = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)
