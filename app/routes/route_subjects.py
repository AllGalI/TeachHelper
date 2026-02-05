import uuid
from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.db import get_async_session
from app.models.model_users import Users
from app.schemas.schema_subjects import SubjectRead
from app.services.service_subjects import ServiceSubjects
from app.utils.oAuth import get_current_user


router = APIRouter(prefix="/subjects", tags=["Subjects"])

@router.post("")
async def create(
    name: str,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user)
):
    service = ServiceSubjects(session)
    return await service.create(name=name, user=user)

@router.get("", response_model=list[SubjectRead])
async def get_all(
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user)
):
    service = ServiceSubjects(session)
    return await service.get_all()
    
@router.patch("/{id}")
async def patch(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user)
):
    service = ServiceSubjects(session)
    return await service.patch(id=id, user=user) 
    
@router.delete("/{id}")
async def delete(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user)
):
    service = ServiceSubjects(session)
    return await service.delete(id=id, user=user) 
