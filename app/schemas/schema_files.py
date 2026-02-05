from typing import TYPE_CHECKING, Optional
import uuid
from pydantic import BaseModel

if TYPE_CHECKING:
    from app.models.model_files import StatusAnswerFile

class UploadFileResponse(BaseModel):
    key: str
    upload_link: str

class IFile(BaseModel):
    key: str
    file: str
    type: str = 'permanent'

class IFileAnswer(BaseModel):
    id: uuid.UUID
    key: str
    file: str
    type: str = 'permanent'
    ai_status: "StatusAnswerFile"

class IFileAnserUpdate(BaseModel):
    id: uuid.UUID | None = None
    key: str
    ai_status: Optional["StatusAnswerFile"] = None


# Вызов model_rebuild() для разрешения forward references
def _rebuild_models():
    """Пересборка моделей для разрешения строковых аннотаций"""
    from app.models.model_files import StatusAnswerFile
    
    # Пересборка моделей, использующих StatusAnswerFile
    IFileAnswer.model_rebuild()
    IFileAnserUpdate.model_rebuild()

_rebuild_models()


def compare_lists(old_list, new_list):
    """
    Сравнивает два списка и возвращает:
    - добавленные элементы (есть в new_list, нет в old_list)
    - удалённые элементы (есть в old_list, нет в new_list)

    Args:
        old_list: старый список
        new_list: новый список

    Returns:
        dict: {'added': [...], 'removed': [...]}
    """
    old_set = set(old_list)
    new_set = set(new_list)

    added = list(new_set - old_set)        # Есть в новом, нет в старом
    removed = list(old_set - new_set)    # Есть в старом, нет в новом

    return {
        'added': added,
        'removed': removed
    }