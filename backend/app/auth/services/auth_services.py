import os
from datetime import timedelta, datetime, timezone
from typing import Annotated
from dotenv import load_dotenv
import jwt
from fastapi import HTTPException, status
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.token import TokenData
from ...models import User
from ...repositories import UserRepository
from ...database import get_db
from ...auth.utils.auth_utils import verify_password, create_jwt
from ...config import settings
load_dotenv()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def authenticate_user(username: str, password: str, db: AsyncSession):
    user = await UserRepository(db).get_user_by_username(username)
    if user:
        hashed_password = user.password
    else:
        hashed_password = os.getenv("DUMMY_HASHED_PASSWORD")
    
    is_verified = verify_password(password, hashed_password)
    if not is_verified:
        return False
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db:AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, key=settings.auth_jwt.secret_key, algorithms=[settings.auth_jwt.algorithm])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = await UserRepository(db).get_user_by_username(token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    return current_user