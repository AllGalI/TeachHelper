from enum import Enum
import uuid
from pydantic import BaseModel, EmailStr

from app.models.model_users import RoleUser
from app.services.schema_base import BaseModelConfig

class UserRegRole(str, Enum):
    teacher = "teacher"
    student = "student"

class UserBase(BaseModelConfig):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr

class UserRegister(UserBase):
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    role: UserRegRole

    model_config = { 
        "json_schema_extra": {
            "example": {
                "email": "ivan@example.com",
                "first_name": "ivan",
                "last_name": "ivanov",
                "password": "123456",
                "role": "teacher"
            }
        }
    }

class EmailBodyDTO(BaseModelConfig):
    email: EmailStr



class UserLogin(BaseModel):
    email: EmailStr
    password: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "ivan@example.com",
                "password": "123456",
            }
        }
    }

class ConfirmReset(BaseModel):
    email: EmailStr
    code: str

class UserResetPassword(BaseModel):
    token: str
    password: str

class UserRead(UserBase):
    id: uuid.UUID
    role: RoleUser
    is_verificated: bool
    
    model_config = {
        "from_attributes": True 
    }

class CodeDTO(BaseModel):
    email: EmailStr
    code: str

class UserToken(BaseModel):
    token_type: str|None = None
    access_token: str|None = None
