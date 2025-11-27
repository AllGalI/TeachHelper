from datetime import timedelta
from random import randint
import uuid
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.config_app import settings
from app.models.model_users import Users
from app.repositories.repo_user import RepoUser
from app.schemas.schema_auth import UserRead, UserRegister, UserResetPassword, UserToken

from app.utils.oAuth import create_access_token, decode_token
from app.utils.password import verify_password, get_password_hash
from fastapi.security import OAuth2PasswordRequestForm
from app.services.service_mail import ServiceMail
from app.services.service_base import ServiceBase

class ServiceAuth(ServiceBase):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.mail = ServiceMail()


    async def register(self, user: UserRegister):
        try:
            repo = RepoUser(self.session)
            if await repo.email_exists(user.email):
                raise HTTPException(status.HTTP_409_CONFLICT, "User with this email already exists")

            user_db = Users(
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                password=get_password_hash(user.password),
                role=user.role,
            )

            db_user = await repo.create(user_db)
            await self.session.commit()
            return UserRead.model_validate(db_user)
        except HTTPException as exc:
            raise

        except:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")


    async def login(self, form_data: OAuth2PasswordRequestForm):
        try:
            repo = RepoUser(self.session)
            if not await repo.email_exists(form_data.username):
                raise HTTPException(status.HTTP_404_NOT_FOUND, "User with this email not exists")

            user = await repo.get_by_email(form_data.username)
            if not verify_password(form_data.password, user.password):
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect password")

            if not user.is_verificated:
                raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Please confirm your email first")

            token = create_access_token({"email": form_data.username}, settings.SECRET)
            return UserToken(token_type="Bearer", access_token=token)

        except HTTPException as exc:
            raise

        except:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")


    async def send_email_confirmation_link(self, email: EmailStr):
        try:
            repo = RepoUser(self.session)
            if not await repo.email_exists(email):
                raise HTTPException(status.HTTP_404_NOT_FOUND, "User with this email not exists")

            user = await repo.get_by_email(email)
            if user.is_verificated:
                raise HTTPException(status.HTTP_409_CONFLICT, detail="User is already verificated")

            token = create_access_token({"email": email}, settings.SECRET_CONFIRM_KEY, timedelta(seconds=100))
            verify_link = f"{settings.FRONT_URL}/confirm_email?token=Bearer {token}"
            await ServiceMail.send_mail_async(email, "Подтверждение почты", "template_verification_code.html", {"verify_link": verify_link})

            return {"message": "Письмо отправлено"}
        except HTTPException as exc:
            raise

        except:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")


    async def confirm_email(self, token: str):
        try:
            payload = decode_token(token, settings.SECRET_CONFIRM_KEY)

            email = payload.get("email")
            if not email:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid token")

            repo = RepoUser(self.session)
            user = await repo.get_by_email(email)
            if user is None: 
                raise HTTPException(status.HTTP_404_NOT_FOUND, "User with this email not exists")

            user.is_verificated = True
            await self.session.commit()
            return {"message": "Почта подтверждена"}    
        except HTTPException as exc:
            raise

        except:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")



    async def forgot_password(self, email: EmailStr):
        try:
            repo = RepoUser(self.session)
            if not await repo.email_exists(email):
                raise HTTPException(status.HTTP_404_NOT_FOUND, "User with this email not exists")

            user = await repo.get_by_email(email)
            if not user.is_verificated:
                raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Please confirm your email first")

            token = create_access_token({"email": email}, settings.SECRET_RESET_KEY, timedelta(seconds=60))
            reset_link = f"{settings.FRONT_URL}/reset_password?token=Bearer {token}"
            await ServiceMail.send_mail_async(email, "Сброс пароля", "template_reset_password.html", {"name": user.first_name, "reset_link": reset_link})

            return {"message": "Письмо отправлено"}
        except HTTPException as exc:
            raise

        except:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")
    
    async def reset_password(self, reset_data: UserResetPassword):
        try:
            payload = decode_token(reset_data.token, settings.SECRET_RESET_KEY)
            email = payload.get("email")
            if not email:
                raise HTTPException(status_code=400, detail="Invalid token")

            repo = RepoUser(self.session)
            user = await repo.get_by_email(email)

            if user is None: 
                raise HTTPException(status.HTTP_404_NOT_FOUND, "User with this email not exists")
            
            await repo.update(user.id, {"password": get_password_hash(reset_data.password)})
            await self.session.commit()
            return {"message": "Пароль обновлён"}
        except HTTPException as exc:
            raise

        except:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")


    async def delete(self, email: EmailStr, id: uuid.UUID):
        try:
            user_db = await self.session.get(Users, id)

            if email != user_db.email:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Input right account email for deleting")
            
            if user_db is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
            
            await self.session.delete(user_db)
            await self.session.commit()
            return JSONResponse(
                content={"status": "ok"},
                status_code=status.HTTP_200_OK
            )
        except HTTPException as exc:
            raise

        except:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")