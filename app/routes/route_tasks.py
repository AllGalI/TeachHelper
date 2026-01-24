import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.db import get_async_session
from app.models.model_users import Users
from app.schemas.schema_tasks import *
from app.services.service_tasks import ServiceTasks
from app.services.service_work import ServiceWork
from app.utils.oAuth import get_current_user


router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("", response_model=TaskRead)
async def create(
    data: TaskCreate,
    session: AsyncSession = Depends(get_async_session),
    teacher: Users = Depends(get_current_user)
):
    service = ServiceTasks(session)
    return await service.create(teacher, data)


@router.get("/filters", response_model=TasksFiltersReadSchema)
async def get_filters(
    session: AsyncSession = Depends(get_async_session),
    teacher: Users = Depends(get_current_user)
):
    """Получение доступных фильтров для списка задач: список предметов и задач"""
    service = ServiceTasks(session)
    return await service.get_filters(teacher)


@router.get("", response_model=list[TasksListItem])
async def get_all(
    filters: TasksFilters = Depends(),
    session: AsyncSession = Depends(get_async_session),
    teacher: Users = Depends(get_current_user)
):
    service = ServiceTasks(session)
    return await service.get_all(teacher, filters)

@router.get("/{id}", response_model=TaskRead)
async def get(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    teacher: Users = Depends(get_current_user)
):
    service = ServiceTasks(session)
    return await service.get(id, teacher)

@router.post("/{id}/start")
async def create_works(
    id: uuid.UUID,
    students_ids: list[uuid.UUID],
    classrooms_ids: list[uuid.UUID] | None = None,
    session: AsyncSession = Depends(get_async_session),
    teacher: Users = Depends(get_current_user)
):
    service = ServiceWork(session)
    return await service.create_works(id, teacher, students_ids, classrooms_ids)

@router.put("/{id}", response_model=TaskRead)
async def update(
    id: uuid.UUID,
    data: TaskUpdate,
    session: AsyncSession = Depends(get_async_session),
    teacher: Users = Depends(get_current_user)
):
    service = ServiceTasks(session)
    return await service.update(id, data, teacher)


@router.delete("/{id}")
async def delete(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    teacher: Users = Depends(get_current_user)
):
    service = ServiceTasks(session)
    return await service.delete(id, teacher)

