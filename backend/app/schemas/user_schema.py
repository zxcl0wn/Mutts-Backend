from pydantic import BaseModel


class UserBase(BaseModel):
    username: str


class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: str|None = None
    password: str|None = None