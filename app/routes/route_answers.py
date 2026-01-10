import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_session
from app.models.model_users import Users
from app.services.service_answers import ServiceAnswers
from app.utils.oAuth import get_current_user

 
router = APIRouter(prefix="/teacher/works/{work_id}/answers", tags=["Answers"])

@router.patch("/{answer_id}")
async def teacher_update(
    work_id: uuid.UUID,
    answer_id: uuid.UUID,
    general_comment: str,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user)

):
    service = ServiceAnswers
    return await service.update_comment(
        work_id,
        answer_id,
        general_comment,
        user
    )
