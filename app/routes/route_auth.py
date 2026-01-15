import uuid
from fastapi import APIRouter, Depends, Response
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from app.db import get_async_session
from app.models.model_users import Users
from app.schemas.schema_auth import ConfirmReset, EmailBodyDTO, CodeDTO, UserRegister, UserRead, UserToken, UserResetPassword
from app.schemas.schema_students import UsersPageSchema
from app.services.service_auth import ServiceAuth
from app.utils.oAuth import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserRead)
async def register(user: UserRegister, session: AsyncSession = Depends(get_async_session)):
    service = ServiceAuth(session)
    return await service.register(user)

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_async_session)):
    service = ServiceAuth(session)
    return await service.login(form_data)

@router.post("/send_code")
async def send_code(data: EmailBodyDTO, session: AsyncSession = Depends(get_async_session)):
    service = ServiceAuth(session)
    return await service.send_code(data)

@router.post("/confirm_email")
async def confirm_email(data: CodeDTO, session: AsyncSession = Depends(get_async_session)):
    service = ServiceAuth(session)
    return await service.confirm_email(data)   

@router.post("/forgot_password")
async def forgot_password(email: EmailBodyDTO, session: AsyncSession = Depends(get_async_session)):
    service = ServiceAuth(session)
    return await service.forgot_password(email)

@router.post("/confirm_reset")
async def forgot_password(data: ConfirmReset, session: AsyncSession = Depends(get_async_session)):
    service = ServiceAuth(session)
    return await service.confirm_reset(data)

@router.post("/reset_password")
async def reset_password(data: UserResetPassword, session: AsyncSession = Depends(get_async_session)):
    service = ServiceAuth(session)
    return await service.reset_password(data)

@router.get("/me", response_model=UserRead)
async def me(current_user: Users = Depends(get_current_user)):
    return UserRead.model_validate(current_user)

@router.delete("/{id}")
async def delete(id: uuid.UUID, email: EmailStr, session: AsyncSession = Depends(get_async_session), current_user: Users = Depends(get_current_user)):
    service = ServiceAuth(session)
    return await service.delete(email, id)


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(
        "session", 
        httponly=True, 
        samesite="lax", 
        secure=True # должно совпадать с тем, как создавали
    )
    return {"detail": "Logged out"}