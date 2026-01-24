import uuid
from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.db import get_async_session
from app.models.model_users import Users
from app.schemas.schema_files import UploadFileResponse
from app.services.service_files import ServiceFiles
from app.utils.oAuth import get_current_user


router = APIRouter(prefix="/files", tags=["Files"])

@router.post("/get_upload_link", response_model=UploadFileResponse)
async def upload_file(
    file_name: str,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user)
):
    """
    Загрузка файлов в MinIO и создание записей в PostgreSQL.
    
    - **files**: Список файлов для загрузки
    
    Все файлы сохраняются в единый bucket, указанный в настройках.
    Возвращает список созданных файлов с метаданными.
    """

    service = ServiceFiles(session)
    return await service.create(file_name, user)


@router.delete("/")
async def delete(
    keys: list[str],
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user)
):
    service = ServiceFiles(session)
    return await service.delete(keys)