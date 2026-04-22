from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class TokenData(BaseModel):
    username: str | None = None