import mimetypes
import uuid
from pydantic import BaseModel, field_validator

from app.models.model_files import StatusAnswerFile
from app.models.model_works import StatusWork
from app.schemas.schema_base import BaseModelConfig
from app.schemas.schema_comment import SchemaCommentTypesRead

class AnswerFiles(BaseModel):
    id: uuid.UUID
    key: str
    ai_status: StatusAnswerFile

    @field_validator('ai_status')
    @classmethod
    def validate_ai_status(cls, v: StatusAnswerFile) -> StatusAnswerFile:
        if v in {StatusAnswerFile.pending, StatusAnswerFile.banned}:
            raise ValueError(f"Статус {v.value} нельзя отправлять на бэкенд")
        return v

    @field_validator('key')
    @classmethod
    def validate_mime_type(cls, v: str) -> str:
        # 1. Список разрешенных типов
        allowed_mimetypes = ['image/jpeg', 'image/png']
        
        # 2. Угадываем тип по расширению в ключе (файле)
        mime_type, _ = mimetypes.guess_type(v)
        
        # 3. Проверка
        if mime_type not in allowed_mimetypes:
            raise ValueError(
                f"Недопустимый тип файла для '{v}'. "
                f"Разрешены только: {', '.join(allowed_mimetypes)}"
            )
            
        return v

class AnswerAI(BaseModel):
    id: uuid.UUID
    files: list[AnswerFiles]

class SchemaIncoming(BaseModel):
    work_id: uuid.UUID
    task_id: uuid.UUID
    status: StatusWork
    comment_types: list[SchemaCommentTypesRead]
    answers: list[AnswerAI]



import uuid

from app.schemas.schema_base import BaseModelConfig


class Coordinates(BaseModelConfig):
    x1: float
    y1: float
    x2: float
    y2: float

class CommentOutgoing(BaseModelConfig):
    answer_id: uuid.UUID
    answerfile_id: uuid.UUID
    description: str
    type_id: uuid.UUID
    coordinates: list[Coordinates]
    files: list[str] = []
    human: bool = False

class AnswerOutgoing(BaseModelConfig):
    id: uuid.UUID
    comments: list[CommentOutgoing]

class SchemaOutgoing(BaseModelConfig):
    answers: list[AnswerOutgoing]