from sqlalchemy.ext.asyncio import AsyncSession
from ..models import User
from ..auth.utils.auth_utils import get_password_hash
from sqlalchemy import select


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db


    async def get_all(self) -> list[User]:
        users = await self.db.execute(
            select(User)
        )
        return users.scalars().all()


    async def get_by_id(self, user_id: int) -> User|None:
        user = await self.db.execute(
            select(User).where(User.id==user_id)
        )
        return user.scalar_one_or_none()


    async def create(self, user: dict) -> User:
        hashed_password = get_password_hash(user["password"])
        new_user = User(
            username=user["username"],
            password=hashed_password
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user


    async def update(self, user: User, user_data: dict) -> User:
        hashed_password = get_password_hash(user["password"])

        for key, value in user_data.items():
            if value is not None:
                if key == "password":
                    setattr(user, key, hashed_password)
                else:
                    setattr(user, key, value)

        await self.db.commit()
        await self.db.refresh(user)
        return user


    async def delete(self, user: User) -> User:
        await self.db.delete(user)
        await self.db.commit()
        return user


    async def get_user_by_username(self, username: str) -> User|None:
        user = await self.db.execute(
            select(User).where(User.username==username)
        )
        return user.scalar_one_or_none()


    async def get_best_users_by_rating(self) -> list[User]:
        best_users = await self.db.execute(
            select(User).order_by(User.rating.desc()).limit(50)
        )
        return best_users.scalars().all()