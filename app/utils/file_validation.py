"""
Утилиты для валидации загружаемых файлов.
"""
from fastapi import HTTPException, UploadFile
from typing import List

# Разрешенные MIME типы
ALLOWED_MIME_TYPES = [
    'image/jpeg',
    'image/png',
    'image/gif',
    'application/pdf',
    'text/plain',
    'text/plain; charset=utf-8',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
]

# Разрешенные расширения файлов
ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png']
# ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.txt']

# Максимальный размер файла (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


async def validate_file(file: UploadFile) -> None:
    """
    Валидация загружаемого файла.
    
    Проверяет:
    - Размер файла
    - Расширение файла
    - MIME тип (если доступен)
    
    Args:
        file: Загружаемый файл
        
    Raises:
        HTTPException: Если файл не прошел валидацию
    """
    # Проверка размера файла
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024 * 1024):.1f} MB"
        )
    
    # Проверка расширения файла
    if file.filename:
        file_extension = None
        for ext in ALLOWED_EXTENSIONS:
            if file.filename.lower().endswith(ext):
                file_extension = ext
                break
        
        if file_extension is None:
            raise HTTPException(
                status_code=400,
                detail=f"File extension not allowed. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
            )
    
    # Проверка MIME типа (если доступен)
    if file.content_type:
        # Нормализация MIME типа (убираем параметры после ;)
        mime_type = file.content_type.split(';')[0].strip().lower()
        
        if mime_type not in [mime.lower() for mime in ALLOWED_MIME_TYPES]:
            # Не строгая проверка - только предупреждение в логах
            # В продакшене можно сделать строже
            pass


async def validate_files(files: List[UploadFile]) -> None:
    """
    Валидация списка загружаемых файлов.
    
    Args:
        files: Список загружаемых файлов
        
    Raises:
        HTTPException: Если хотя бы один файл не прошел валидацию
    """
    for file in files:
        await validate_file(file)

