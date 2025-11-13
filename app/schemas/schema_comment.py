import uuid
from pydantic import BaseModel

from app.schemas.schema_files import FileSchema


class CommentCreate(BaseModel):
    answer_id: uuid.UUID
    type_id: uuid.UUID
    description: str|None = None


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
