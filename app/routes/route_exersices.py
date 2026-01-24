import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.db import get_async_session
from app.models.model_users import Users
from app.services.service_tasks import ServiceTasks
from app.utils.oAuth import get_current_user


router = APIRouter(prefix="/tasks", tags=["Tasks"])