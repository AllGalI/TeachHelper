import uuid
from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.db import get_async_session
from app.models.model_users import Users
from app.schemas.schema_comment import CommentCreate, CommentUpdate
from app.services.service_comments import ServiceComments
from app.utils.oAuth import get_current_user


router = APIRouter(prefix="/comments", tags=["Comments"])


@router.post("")
async def create_comments(
    comment: CommentCreate,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user)
):
    service = ServiceComments(session)
    return await service.create(
        comment,
        user
    )

@router.put("/{comment_id}")
async def update_comment(
    comment_id: uuid.UUID,
    data: CommentUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user)
):
    service = ServiceComments(session)
    return await service.update(comment_id, data, user)

@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user)
):
    service = ServiceComments(session)
    return await service.delete(comment_id, user)
