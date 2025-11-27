import uuid
from pydantic import BaseModel

from app.models.model_comments import Coordinates
from app.schemas.schema_files import FileSchema
from app.services.schema_base import BaseModelConfig


class Coordinates(BaseModelConfig):
    x1: float
    y1: float
    x2: float
    y2: float

class AICommentDTO(BaseModelConfig):
    answer_id: uuid.UUID
    image_file_id: uuid.UUID
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
    image_file_id: uuid.UUID
    description: str
    type_id: uuid.UUID
    coordinates: list[Coordinates]


class CommentRead(CommentCreate):
    id: uuid.UUID
    answer_id: uuid.UUID
    type_id: uuid.UUID
    description: str
    files: list[FileSchema]|None = None

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
