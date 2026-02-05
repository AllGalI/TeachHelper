import uuid
from fastapi import Query
from typing import Optional
from pydantic import Field

from app.schemas.schema_base import BaseModelConfig

class NameFilter(BaseModelConfig):
    id: uuid.UUID
    name: str

class FiltersClassroomJournalResponse(BaseModelConfig):
    start_date: str
    end_date: str
    classrooms: list[NameFilter]
    tasks: list[NameFilter]

class FiltersClassroomJournalRequest(BaseModelConfig):
    start_date: Optional[str] = Field(Query(None))
    end_date: Optional[str] = Field(Query(None))
    classroom: uuid.UUID
    task: Optional[uuid.UUID] = Field(Query(None))


class StudentWorkPerformanse(BaseModelConfig):
    id: uuid.UUID
    name: str
    status: str

class StudentsPerformanseItem(BaseModelConfig):
    full_name: str
    verificated_works_count: int
    average_score: int
    works: list[StudentWorkPerformanse]

class ClassroomPerformanse(BaseModelConfig):
    id: str
    name: str
    students: list[StudentsPerformanseItem]
