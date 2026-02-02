from datetime import datetime
from pydantic import BaseModel
import uuid

from app.schemas.schema_base import BaseModelConfig


class PlanCreate(BaseModel):
    name: str
    verifications_count: int
    amount: int


class PlanRead(BaseModelConfig):
    id: uuid.UUID
    name: str
    verifications_count: int
    amount: int
    expiration_days: int