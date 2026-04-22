import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from ..services.auth_services import authenticate_user, get_current_user
from ...auth.utils.auth_utils import create_access_token, create_refresh_token
from fastapi.security import OAuth2PasswordRequestForm
from ..models import Token
from ...config import settings
from ...database import get_db
from ...models import User
from ...schemas import UserCreate, UserResponse
from ...services import UserService

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post("/register")
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    return await service.create(user_data)


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db)
) -> Token:
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)
    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=Token)
async def refresh_access_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    payload = jwt.decode(refresh_token, key=settings.auth_jwt.secret_key, algorithms=[settings.auth_jwt.algorithm])
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_username = payload.get("sub")
    if user_username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user = await UserService(db).get_user_by_username(user_username)

    new_access_token = create_access_token(user)

    return {
        "access_token": new_access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user