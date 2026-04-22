from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import User
from ..repositories import UserRepository
from ..schemas.user_schema import UserResponse, UserCreate, UserUpdate
from sqlalchemy.exc import IntegrityError


class UserService:
    def __init__(self, db: AsyncSession):
        self.user_repository = UserRepository(db)


    async def get_all(self) -> list[UserResponse]:
        users = await self.user_repository.get_all()
        return [UserResponse.model_validate(user) for user in users]


    async def get_by_id(self, user_id: int) -> UserResponse:
        user = await self.user_repository.get_by_id(user_id)
        return UserResponse.model_validate(user)


    async def create(self, user: UserCreate) -> UserResponse:
        try:
            new_user = await self.user_repository.create(user.model_dump())
            return UserResponse.model_validate(new_user)
        except IntegrityError:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")


    async def update(self, user_id: int, user_data: UserUpdate) -> UserResponse:  # TODO
        ...


    async def delete(self, user_id: int) -> UserResponse:  # TODO
        ...


    async def get_user_by_username(self, username: str) -> UserResponse:
        user = await self.user_repository.get_user_by_username(username)
        return UserResponse.model_validate(user)