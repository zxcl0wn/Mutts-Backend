from functools import lru_cache
from pydantic import BaseModel
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
load_dotenv()


class DBSettings(BaseModel):
    url: str = f'postgresql+asyncpg://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}'
    echo: bool = False


class AuthJWT(BaseModel):
    secret_key: str = os.getenv("SECRET_KEY")
    algorithm: str = os.getenv("ALGORITHM")
    dummy_password: str = os.getenv("DUMMY_HASHED_PASSWORD")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
    refresh_token_expire_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS"))


class RedisSettings(BaseModel):
    url: str = "redis://localhost:6379/0"


class Settings(BaseSettings):
    db: DBSettings = DBSettings()
    auth_jwt: AuthJWT = AuthJWT()
    redis: RedisSettings = RedisSettings()


@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
