
from pydantic import BaseModel

class UploadFileResponse(BaseModel):
  key: str
  upload_link: str

class IFile(BaseModel):
  key: str
  file: str
  type: str = 'permanent'


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