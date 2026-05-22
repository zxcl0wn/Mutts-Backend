from sqlalchemy.ext.asyncio import AsyncSession
from ..models import User
from ..auth.utils.auth_utils import get_password_hash
from sqlalchemy import select
from ..core.calculate_rating import calculate_new_rating


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


    async def update_match_stats(self, player1: str, player2: str, winner: str) -> tuple[int, int]:
        p1 = await self.get_user_by_username(player1)
        p2 = await self.get_user_by_username(player2)
        if not p1 or not p2:
            return (0, 0)

        score_A = 0.5 if winner == "draw" else (1.0 if winner == player1 else 0.0)
        new_rating1, new_rating2 = calculate_new_rating(p1.rating, p2.rating, score_A)
        p1.rating = new_rating1
        p2.rating = new_rating2

        if winner == "draw":
            p1.draw_count += 1
            p2.draw_count += 1
        elif winner == player1:
            p1.win_count += 1
            p2.lose_count += 1
        else:
            p1.lose_count += 1
            p2.win_count += 1
        await self.db.commit()
        return (new_rating1, new_rating2)


    async def get_best_users_by_rating(self) -> list[User]:
        best_users = await self.db.execute(
            select(User).order_by(User.rating.desc()).limit(50)
        )
        return best_users.scalars().all()