import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.db import get_async_session
from app.models.model_users import Users
from app.services.service_assessments import ServiceAssessments
from app.utils.oAuth import get_current_user


router = APIRouter(prefix="/worsk/{work_id}/answers/{answer_id}/assessments", tags=["Answers"])

@router.put("/{id}")
async def update(
    work_id: uuid.UUID,
    answer_id: uuid.UUID,
    id: uuid.UUID,
    points: int,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user)
):
    service = ServiceAssessments(session)
    return await service.update(work_id, answer_id, id, points, user,)