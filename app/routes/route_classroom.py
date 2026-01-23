

import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_session
from app.models.model_users import Users
from app.schemas.schema_classroom import SchemaClassroom, SchemaClassroomsFilter
from app.services.service_classroom import ServiceClassroom
from app.utils.oAuth import get_current_user


router = APIRouter(prefix="/classrooms", tags=["Classroom"])

@router.post("")
async def create_classroom(
    name: str,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user)
):
    service = ServiceClassroom(session)
    return await service.create(name, user)

@router.get("", response_model=list[SchemaClassroom])
async def get_all(
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user)
):
    service = ServiceClassroom(session)
    return await service.get_all(user)


@router.patch('/{id}')
async def update(
    id: uuid.UUID,
    name: str,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user)
):
    service = ServiceClassroom(session)
    return await service.update(id, name)


@router.delete('/{id}')
async def delete(
    id: uuid.UUID,
    delete_students: bool = False,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user)
):
    service = ServiceClassroom(session)
    return await service.delete(id, delete_students, user)
    
# @router.get('/{id}')
# async def get(
#     id: uuid.UUID,
#     session: AsyncSession = Depends(get_async_session),
#     current_user: Users = Depends(get_current_user)
# ):
#     service = ServiceClassroom(session)
#     return await service.get(id, current_user)