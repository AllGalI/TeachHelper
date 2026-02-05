from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.db import get_async_session
from app.models.model_users import Users
from app.schemas.schema_plan import PlanRead
from app.services.service_plans import ServicePlans

router = APIRouter(
    prefix="/plans",
    tags=["plans"],
)



@router.get("/", response_model=list[PlanRead])
async def get_plans(
    session: AsyncSession = Depends(get_async_session),
):
    service = ServicePlans(session)
    return await service.get_all()