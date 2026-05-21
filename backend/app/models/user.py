from sqlalchemy import Column, Integer, String
from ..database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    username = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)

    def __repr__(self):
        return f'<User(id={self.id}, username={self.username})>'
