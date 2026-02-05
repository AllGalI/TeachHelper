import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.db import get_async_session
from app.models.model_users import Users
from app.schemas.schema_subscription import SubscriptionCancel, SubscriptionStartPeriodRequest, SubscriptionRead
from app.services.service_subscription import ServiceSubscription
from app.utils.oAuth import get_current_user


router = APIRouter(
    prefix="/subscriptions",
    tags=["Subscriptions"],
)


@router.post("/cancel")
async def cancel_subscription(
    data: SubscriptionCancel,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user)
):
    """
    Отмена подписки с проверкой условий возврата средств.
    
    Условия возврата:
    - В течение 14 дней с момента оплаты
    - Использование не превышает лимит для тарифа
    """
    service = ServiceSubscription(session)
    return await service.cancel_subscription(data, user.id)


@router.post("/start-period", response_model=SubscriptionRead)
async def start_new_period(
    data: SubscriptionStartPeriodRequest,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user),
):
    """
    Начало нового периода подписки.
    Сбрасываются used_checks и self_writing,
    обновляются started_at и finish_at по выбранному плану.
    """
    service = ServiceSubscription(session)
    return await service.start_new_period(data, user.id)
