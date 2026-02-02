from datetime import datetime
from pydantic import BaseModel
import uuid

from app.schemas.schema_base import BaseModelConfig
from app.schemas.schema_plan import PlanRead


class SubscriptionCreate(BaseModel):
    """Схема для создания подписки (внутреннее использование)."""
    user_id: uuid.UUID
    plan_id: uuid.UUID
    email_hash: str
    used_checks: int = 0
    started_at: datetime
    finish_at: datetime
    self_writing: bool = False


class SubscriptionUpdate(BaseModelConfig):
    """Схема для обновления подписки."""
    plan_id: uuid.UUID
    used_checks: int
    finish_at: datetime


class SubscriptionRead(BaseModelConfig):
    """Схема для чтения подписки."""
    id: uuid.UUID
    user_id: uuid.UUID | None
    used_checks: int
    started_at: datetime
    finish_at: datetime
    self_writing: bool
    created_at: datetime | None
    plan: PlanRead | None = None


class SubscriptionStartPeriodRequest(BaseModel):
    """
    Схема запроса для начала нового периода подписки.
    Сбрасываются used_checks и self_writing, обновляются started_at и finish_at.
    """
    id: uuid.UUID  # ID подписки (одна запись на пользователя)
    plan_id: uuid.UUID
    user_id: uuid.UUID  # для проверки принадлежности подписки пользователю


class SubscriptionCancel(BaseModel):
    """Схема для отмены подписки."""
    id: uuid.UUID
