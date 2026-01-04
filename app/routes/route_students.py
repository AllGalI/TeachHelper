import os
import uuid
from fastapi import APIRouter, Depends

from app.config.config_app import settings
from app.db import get_async_session
from app.models.model_users import Users
from app.schemas.schema_students import UsersPageSchema, StudentsReadSchemaTeacher
from app.services.teacher.service_students import ServiceStudents
from app.utils.oAuth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix='/students', tags=["Students"])

@router.get("", response_model=UsersPageSchema)
async def get_all(
    session: AsyncSession = Depends(get_async_session),
    current_user: Users = Depends(get_current_user)
    ):
    service = ServiceStudents(session)
    return await service.get_all(current_user)


@router.get("/filters", response_model=StudentsReadSchemaTeacher)
async def get_filters(
    session: AsyncSession = Depends(get_async_session),
    current_user: Users = Depends(get_current_user)
):
    """Получение доступных фильтров для списка студентов: список студентов и классов"""
    service = ServiceStudents(session)
    return await service.get_filters(current_user)


@router.get("/{id}")
async def get_performans_data(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user: Users = Depends(get_current_user)
    ):
    service = ServiceStudents(session)
    return await service.get_performans_data(student_id=id, user=current_user)



@router.patch("/{id}/move_to_class")
async def move_to_class(
    id: uuid.UUID,
    classroom_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user: Users = Depends(get_current_user)
    ):
    service = ServiceStudents(session)
    return await service.move_to_class(student_id=id, classroom_id=classroom_id, user=current_user)


@router.patch("/{id}/remove_from_class")
async def remove_from_class(
    id: uuid.UUID,
    classroom_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user: Users = Depends(get_current_user)
    ):
    service = ServiceStudents(session)
    return await service.remove_from_class(student_id=id, classroom_id=classroom_id, user=current_user)


@router.delete("/{id}")
async def delete(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user: Users = Depends(get_current_user)
    ):
    service = ServiceStudents(session)
    return await service.delete(student_id=id, user=current_user)

router2 = APIRouter(prefix='/teachers', tags=["Teachers"])

@router2.get("/invite_link")
async def get_link(
    current_user: Users = Depends(get_current_user)
    ):
    return {"link": f"{settings.FRONT_URL}/t/{current_user.id}"}
    

@router2.post("/{id}")
async def add(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    student: Users = Depends(get_current_user)
):
    service = ServiceStudents(session)
    return await service.add_teacher(id, student)