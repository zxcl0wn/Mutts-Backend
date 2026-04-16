from turtledemo.yinyang import yin

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import settings


engine = create_engine(
    url=settings.db.url,
    connect_args={"check_some_thread": False}  # For SQLite
)
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    ...

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
