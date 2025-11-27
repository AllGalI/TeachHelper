import uuid
from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.models.model_users import Users
from app.schemas.schema_comment import CommentCreate, CommentUpdate, AICommentDTO
from app.services.service_comments import ServiceComments
from app.utils.oAuth import get_current_user


router = APIRouter(prefix="/worsk/{work_id}/answers/{answer_id}/comments", tags=["Answers"])


@router.post("")
async def create_comments(
    work_id: uuid.UUID,
    answer_id: uuid.UUID,
    comments: list[CommentCreate],
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user)
):
    service = ServiceComments(session)
    return await service.create(
        answer_id,
        comments,
        user
    )

@router.put("/{comment_id}")
async def update_comment(
    work_id: uuid.UUID,
    answer_id: uuid.UUID,
    comment_id: uuid.UUID,
    data: CommentUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user)
):
    service = ServiceComments(session)
    return await service.update(comment_id, data, user)

@router.delete("/{comment_id}")
async def delete_comment(
    work_id: uuid.UUID,
    answer_id: uuid.UUID,
    comment_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user)
):
    service = ServiceComments(session)
    return await service.delete(comment_id, user)
