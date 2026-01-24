from typing import Annotated
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.db import get_async_session
from app.models.model_users import Users
from app.schemas.schema_comment import *
from app.schemas.schema_work import SmartFiltersWorkStudent, SmartFiltersWorkTeacher, WorkRead, WorkUpdate, WorksFilterResponseStudent, WorksFilterResponseTeacher
from app.services.service_comments import ServiceComments
from app.services.service_work import ServiceWork, WorkEasyRead
from app.utils.oAuth import get_current_user


router = APIRouter(prefix="/works", tags=["Works"])


@router.get("/teacher/filters", response_model=WorksFilterResponseTeacher)
async def get_filters_teacher(
    filters: Annotated[SmartFiltersWorkTeacher, Depends()],
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user),
):
    service = ServiceWork(session)
    return await service.get_smart_filters_teacher(user, filters)

@router.get("/student/filters", response_model=WorksFilterResponseStudent)
async def get_filters_student(
    filters: Annotated[SmartFiltersWorkStudent, Depends()],
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user),
):
    service = ServiceWork(session)
    return await service.get_smart_filters_student(user, filters)

@router.get("/teacher/list", response_model=list[WorkEasyRead])
async def get_works_list_teacher(
    filters: Annotated[SmartFiltersWorkTeacher, Depends()],
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user),
):
    """Получение списка работ для учителя с применением умных фильтров"""
    service = ServiceWork(session)
    return await service.get_works_list_teacher(user, filters)

@router.get("/student/list", response_model=list[WorkEasyRead])
async def get_works_list_student(
    filters: Annotated[SmartFiltersWorkStudent, Depends()],
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user),
):
    """Получение списка работ для ученика с применением умных фильтров"""
    service = ServiceWork(session)
    return await service.get_works_list_student(user, filters)

@router.get("/{id}", response_model=WorkRead)
async def get(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user)
):
    service = ServiceWork(session)
    return await service.get(id, user)

@router.put("/{work_id}", response_model=WorkRead)
async def update(
    work_id: uuid.UUID,
    data: WorkUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user)
):
    service = ServiceWork(session)
    return await service.update(work_id, data, user)


@router.post("/{work_id}/ai_verification")
async def send_work_to_verification(
    work_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user)
):
    service = ServiceWork(session)
    return await service.send_work_to_verification(work_id, user)


# @router.post("/{work_id}/ai")
# async def create_ai_comments(
#     work_id: uuid.UUID,
#     comments: list[AICommentDTO],
#     session: AsyncSession = Depends(get_async_session),
#     user: Users = Depends(get_current_user)
# ):
#     service = ServiceComments(session)
#     return await service.ai_create(
#         work_id,
#         comments,
#         user
#     )