import uuid
from pydantic import BaseModel
from typing import TYPE_CHECKING, Optional

from app.models.model_comments import Coordinates
from app.schemas.schema_base import BaseModelConfig

if TYPE_CHECKING:
    from app.schemas.schema_files import IFile


class Coordinates(BaseModelConfig):
    x1: float
    y1: float
    x2: float
    y2: float


class CommentCreate(BaseModel):
    answer_id: uuid.UUID
    answerfile_id: uuid.UUID  # Ключ файла ответа из хранилища
    description: str
    type_id: uuid.UUID
    coordinates: list[Coordinates]
    files: list[str]
    human: Optional[bool] = True


class CommentRead(BaseModelConfig):
    id: uuid.UUID
    answer_id: uuid.UUID
    answerfile_id: uuid.UUID  # Ключ файла ответа из хранилища
    description: str
    type_id: uuid.UUID
    coordinates: list[Coordinates]
    files: list["IFile"]  # Ключи файлов из хранилища



class SchemaCommentTypesBase(BaseModelConfig):
    short_name: str
    name: str

class SchemaCommentTypesRead(BaseModelConfig):
    id: uuid.UUID
    short_name: str
    name: str



# Вызов model_rebuild() для разрешения forward references
def _rebuild_models():
    """Пересборка моделей для разрешения строковых аннотаций"""
    from app.schemas.schema_files import IFile
    
    CommentRead.model_rebuild()

_rebuild_models()

class CommentUpdate(BaseModel):
    """
    Схема для обновления комментария.
    
    Поля:
    - type_id: UUID типа комментария (обязательное поле)
    - description: Текст описания комментария (обязательное поле)
    - files: Список ключей файлов в хранилище S3 (опциональное поле)
            При обновлении сравнивается со старым списком файлов,
            удаленные файлы автоматически удаляются из S3
    """
    type_id: uuid.UUID  # ID типа комментария из таблицы comment_types
    description: str  # Текст описания комментария
    files: list[str] | None = None  # Список ключей файлов в S3 (если None, файлы не обновляются)

    model_config = {
        "from_attributes": True,
    }
