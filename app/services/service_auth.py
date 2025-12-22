from datetime import timedelta
from random import randint
import uuid
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from jose import ExpiredSignatureError, jwt, JWTError

from app.config.config_app import settings
from app.models.model_users import Users
from app.repositories.repo_user import RepoUser
from app.schemas.schema_auth import  ConfirmReset, EmailBodyDTO, CodeDTO, UserRead, UserRegister, UserResetPassword

from app.utils.oAuth import create_access_token
from app.utils.password import verify_password, get_password_hash
from fastapi.security import OAuth2PasswordRequestForm
from app.services.service_mail import ServiceMail
from app.services.service_base import ServiceBase
from app.utils.logger import logger
from app.config.redis import red_client

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
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                password=get_password_hash(user.password),
                role=user.role,
            )
            self.session.add(user_db)
            await self.session.flush([user_db])

            response = UserRead.model_validate(user_db)
            await self.session.commit()
            return response

        except HTTPException as exc:
            await self.session.rollback()
            raise

        except Exception as exc:
            logger.exception(exc)
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
            return JSONResponse(content={"token": f"Bearer {token}"})


        except HTTPException as exc:
            await self.session.rollback()
            raise

        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")


    async def send_code(self, data: EmailBodyDTO):
        try:
            repo = RepoUser(self.session)
            if not await repo.email_exists(data.email):
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не существует")

            user = await repo.get_by_email(data.email)
            if user.is_verificated:
                raise HTTPException(status.HTTP_409_CONFLICT, detail="Почта уже подтверждена")
            
            if red_client.get(data.email):
                raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Письмо уже отправлено, попробуйте через минуту")

            code = randint(1000, 9999)
            red_client.set(data.email, code, ex=60)        
            await ServiceMail.send_mail_async(data.email, "Подтверждение почты", "template_verification_code.html", {"code": code})

            return {"message": "Письмо отправлено"}

        except HTTPException as exc:
            await self.session.rollback()
            raise

        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")


    async def confirm_email(self, data: CodeDTO):
        try:
            repo = RepoUser(self.session)
            if not await repo.email_exists(data.email):
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не существует")

            user = await repo.get_by_email(data.email)
            if user.is_verificated:
                raise HTTPException(status.HTTP_409_CONFLICT, detail="Почта уже подтверждена")

            code = str(red_client.get(data.email))
            if code == "None":
              raise HTTPException(status.HTTP_400_BAD_REQUEST, "Код подтверждения просрочился, отправтье новый")

            if code != data.code:
              raise HTTPException(status.HTTP_403_FORBIDDEN, "Неверный код")

            repo = RepoUser(self.session)
            user = await repo.get_by_email(data.email)
            if user is None: 
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователя с такой почтой не существует")

            user.is_verificated = True
            await self.session.commit()
            return {"message": "Почта подтверждена"}    

        except HTTPException as exc:
            await self.session.rollback()
            raise

        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")


    async def forgot_password(self, data: EmailBodyDTO):
        try:
            repo = RepoUser(self.session)
            if not await repo.email_exists(data.email):
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не существует")

            user = await repo.get_by_email(data.email)
            
            if red_client.get(data.email):
                raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Письмо уже отправлено, попробуйте через минуту")

            code = randint(1000, 9999)
            red_client.set(data.email, code, ex=100)        
            await ServiceMail.send_mail_async(data.email, "Сброс пароля", "template_reset_password.html", {"name": user.first_name, "code": code})

            return {"message": "Письмо отправлено"}

        except HTTPException as exc:
            await self.session.rollback()
            raise

        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def confirm_reset(self, data: ConfirmReset):
        try:
            repo = RepoUser(self.session)
            user = await repo.get_by_email(data.email)

            if user is None or not user.is_verificated: 
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не существует")

            code = str(red_client.get(data.email))
            if code == "None":
              raise HTTPException(status.HTTP_400_BAD_REQUEST, "Код подтверждения просрочился, отправтье новый")

            if code != data.code:
              raise HTTPException(status.HTTP_403_FORBIDDEN, "Неверный код")
            
            token = create_access_token({
                "id": str(user.id)
              },
              settings.SECRET_RESET_KEY,
              timedelta(seconds=600)
            )

            return {"token": token}
          
        except HTTPException:
            await self.session.rollback()
            raise
        
        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")      
    
    async def reset_password(self, data: UserResetPassword):
        try:
            payload = jwt.decode(data.token, settings.SECRET_RESET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("id")
            user = await self.session.get(Users, user_id)

            if user is None or not user.is_verificated: 
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не существует")

            user.password = get_password_hash(data.password)
            await self.session.commit()
            return {"message": "Пароль обновлён"}

        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Время для обновления пароля закончилось"
            )

        except HTTPException as exc:
            await self.session.rollback()
            raise

        except Exception as exc:
            logger.exception(exc)
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
            await self.session.rollback()
            raise

        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")