from datetime import datetime, timedelta, timezone
from jose import ExpiredSignatureError, jwt, JWTError
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.model_users import Users
from app.repositories.repo_user import RepoUser
from app.config.config_app import settings
from app.db import get_async_session
from app.schemas.schema_auth import UserRead



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def create_access_token(data: dict, key: str, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, key, algorithm=settings.ALGORITHM)

def decode_token(token: str, key: str, algorithms=[settings.ALGORITHM]):
    if not token.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format (expected 'Bearer <token>')"
        )

    jwt_token = token.split("Bearer ")[1]

    try:
        payload = jwt.decode(token=jwt_token, key=key, algorithms=algorithms)
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
