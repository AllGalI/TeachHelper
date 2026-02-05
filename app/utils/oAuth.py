from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import ExpiredSignatureError, jwt, JWTError
from fastapi import HTTPException, Request, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.model_users import Users
from app.repositories.repo_user import RepoUser
from app.config.config_app import settings
from app.config.db import get_async_session
from app.schemas.schema_auth import UserRead


class OAuth2PasswordBearerWithCookie(OAuth2PasswordBearer):
    async def __call__(self, request: Request) -> Optional[str]:
        # 1. Пытаемся достать токен из Cookies
        token: str = request.cookies.get("session")
        # 2. Если в куках нет, ищем в заголовках (для Swagger)
        if not token:
            # Вызываем родительский метод, который умеет работать с Header Authorization
            token = await super().__call__(request)
            
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return token

oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/auth/login")

def create_access_token(data: dict, key: str, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, key, algorithm=settings.ALGORITHM)

def decode_token(token: str, key: str, algorithms=[settings.ALGORITHM]):
    try:
        payload = jwt.decode(token, key, algorithms)
        return payload

    except ExpiredSignatureError:
        # Срок действия токена истёк
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )

    except JWTError:
        # Любая другая JWT ошибка (подпись неверна, токен повреждён и т.п.)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed token"
        )

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_async_session)) -> Users:
    repo = RepoUser(db)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET, algorithms=[settings.ALGORITHM])
        email: str = payload.get("email")
        if email is None:
            raise credentials_exception

    except JWTError as exc:
        raise credentials_exception

    user = await repo.get_by_email(email=email)
    if user is None:
        raise credentials_exception

    return user
