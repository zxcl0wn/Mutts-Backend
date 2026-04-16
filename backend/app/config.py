from pydantic import BaseModel
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
load_dotenv()


class DBSettings(BaseModel):
    url = "sqlite:///./mutts_test.db"
    echo: bool = True


class AuthJWT(BaseModel):
    ...


class Settings(BaseSettings):
    db: DBSettings = DBSettings()
    auth_jwt: AuthJWT = AuthJWT()


settings = Settings()
