from bcrypt import hashpw, gensalt, checkpw
import jwt
from fastapi import HTTPException, status
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
from ...config import settings
from ...models import User
load_dotenv()


TOKEN_TYPE_FIELD = "type"
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def get_password_hash(password: str) -> str:
    return hashpw(password.encode("utf-8"), gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def encode_jwt(
        payload: dict,
        secret_key: str = os.getenv("SECRET_KEY"),
        algorithm=os.getenv("ALGORITHM"),
        expire_minutes: int = settings.auth_jwt.access_token_expire_minutes,
        expire_timedelta: timedelta | None = None
) -> str:
    to_encode = payload.copy()
    if expire_timedelta:
        expire = datetime.now(timezone.utc) + expire_timedelta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)

    to_encode.update(exp=expire)
    encoded = jwt.encode(
        to_encode,
        key=secret_key,
        algorithm=algorithm,
    )
    return encoded


def create_jwt(
    token_type: str,
    token_data: dict,
    expire_minutes: int = settings.auth_jwt.access_token_expire_minutes,
    expire_timedelta: timedelta | None = None,
) ->  str:
    jwt_payload = {
        TOKEN_TYPE_FIELD: token_type
    }
    jwt_payload.update(token_data)

    return encode_jwt(
        payload=jwt_payload,
        expire_minutes=expire_minutes,
        expire_timedelta=expire_timedelta,
    )


def create_access_token(user: User):
    jwt_payload = {
        "sub": user.username,

    }
    return create_jwt(
        token_type=ACCESS_TOKEN_TYPE,
        token_data=jwt_payload,
        expire_minutes=settings.auth_jwt.access_token_expire_minutes,
    )


def create_refresh_token(user: User) -> str:
    jwt_payload = {
        "sub": user.username,
    }
    return create_jwt(
        token_type=REFRESH_TOKEN_TYPE,
        token_data=jwt_payload,
        expire_timedelta=timedelta(days=settings.auth_jwt.refresh_token_expire_days),
    )


async def verify_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token,
            key=settings.auth_jwt.secret_key,
            algorithms=[settings.auth_jwt.algorithm]
        )

        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: no username"
            )
        return username

    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
