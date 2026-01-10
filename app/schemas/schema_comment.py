import uuid
from pydantic import BaseModel

from app.models.model_comments import Coordinates
from app.services.schema_base import BaseModelConfig


class Coordinates(BaseModelConfig):
    x1: float
    y1: float
    x2: float
    y2: float

class AICommentDTO(BaseModelConfig):
    answer_id: uuid.UUID
    answer_file_key: str  # Ключ файла ответа из хранилища
    description: str
    type_id: uuid.UUID
    coordinates: list[Coordinates]

class AIAnswerDTO(BaseModelConfig):
    id: uuid.UUID
    comments: list[AICommentDTO]

class AIWorkDTO(BaseModelConfig):
    id: uuid.UUID
    answers: list[AIAnswerDTO]


class CommentCreate(BaseModel):
    answer_id: uuid.UUID
    answer_file_key: str  # Ключ файла ответа из хранилища
    description: str
    type_id: uuid.UUID
    coordinates: list[Coordinates]


class CommentRead(CommentCreate):
    id: uuid.UUID
    file_keys: list[str] | None = None  # Ключи файлов из хранилища

    model_config = {
        "from_attributes": True,
    }

# сначала удаляем файл потом получаем комментарий
class CommentUpdate(BaseModel):
    type_id: uuid.UUID
    description: str

    model_config = {
        "from_attributes": True,
    }
