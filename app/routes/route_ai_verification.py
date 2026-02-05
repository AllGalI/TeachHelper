from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.db import get_async_session
from app.models.model_users import Users
from app.schemas.schema_AI import SchemaIncomingFront
from app.services.service_AI import ServiceAI
from app.utils.oAuth import get_current_user


router = APIRouter(
    prefix="/ai_verification",
    tags=["AI Verification"],
)

@router.post("/")
async def ai_verification(
    data: SchemaIncomingFront,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user)
):
    service = ServiceAI(session)
    return await service.ai_verification(data, user)