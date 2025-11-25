from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.models.model_works import StatusWork
from app.models.model_users import Users
from app.schemas.schema_comment import *
from app.schemas.schema_work import WorkAllFilters
from app.services.pika_service.htr_client import ClientHTRRpc, WorkRequestDTO
from app.services.service_comments import ServiceComments
from app.services.service_files import ServiceFiles
from app.services.service_work import ServiceWork, WorkEasyRead, WorkUpdate
from app.utils.oAuth import get_current_user


router = APIRouter(prefix="/works", tags=["Works"])


@router.get("/teacher", response_model=list[WorkEasyRead])
async def get_all_teacher(
    subject_id: Optional[uuid.UUID] = None,
    students_ids: Optional[list[uuid.UUID]] = Query(None),
    classrooms_ids: Optional[list[uuid.UUID]] = Query(None),
    status_work: Optional[StatusWork] = None,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user),
):

    service = ServiceWork(session)
    return await service.get_all_teacher(
        user=user,
        subject_id=subject_id,
        students_ids=students_ids,
        classrooms_ids=classrooms_ids,
        status_work=status_work,
    )
    
@router.get("/student", response_model=list[WorkEasyRead])
async def get_all_student(
    subject_id: uuid.UUID|None = None,
    status_work: StatusWork|None = None,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user)
):
    service = ServiceWork(session)
    return await service.get_all_student(
        user,
        subject_id,
        status_work,
    )

@router.get("/{id}")
async def get(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user)
):
    service = ServiceWork(session)
    return await service.get(id)

@router.patch("/{work_id}")
async def update(
    id: uuid.UUID,
    status: StatusWork,
    conclusion: str|None = None,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user)
):
    service = ServiceWork(session)
    return await service.update(id, status, conclusion, user)


# router = APIRouter(prefix="/works/{work_id}", tags=["Works"])

# @router.post("/ai_verification")
@router.post("/{work_id}/ai_verification")
async def verificate_work(
    work_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user)
):
    service = ServiceWork(session)
    return await service.verificate_work(work_id, user)