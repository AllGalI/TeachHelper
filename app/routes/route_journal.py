from typing import Annotated
from fastapi import APIRouter, Depends

from app.config.db import get_async_session
from app.schemas.schema_journal import ClassroomPerformanse, FiltersClassroomJournalRequest, FiltersClassroomJournalResponse
from app.services.service_journal import ServiceJournal
from app.utils.oAuth import get_current_user



router = APIRouter(prefix='/journal', tags=['Journal'])


@router.get("/filters", response_model=FiltersClassroomJournalResponse)
async def get_filters(
    session = Depends(get_async_session),
    user = Depends(get_current_user)
):
    service = ServiceJournal(session)
    return await service.get_filters(user)

@router.get('', response_model=ClassroomPerformanse)
async def get(
    filters: Annotated[FiltersClassroomJournalRequest, Depends()],
    session = Depends(get_async_session),
    user = Depends(get_current_user)
):
  service = ServiceJournal(session)
  return await service.get(filters, user)