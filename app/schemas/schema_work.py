

from datetime import datetime
import uuid
from fastapi import Query
from pydantic import BaseModel, Field

from app.models.model_works import StatusWork
from app.schemas.schema_comment import CommentRead
from app.schemas.schema_tasks import TaskRead
from app.services.schema_base import BaseModelConfig


class WorkAllFilters(BaseModel):
    subject_id: uuid.UUID|None = None
    students_ids: list[uuid.UUID]|None = None
    classrooms_ids: list[uuid.UUID]|None = None
    status_work: StatusWork|None = None

class AssessmentBase(BaseModel):
    answer_id:    uuid.UUID
    criterion_id: uuid.UUID

class AssessmentRead(BaseModel):
    id:        uuid.UUID
    points: int

    model_config = {
        "from_attributes": True,
    }


class AssessmentUpdate(BaseModel):
    id:        uuid.UUID|None = None
    points: int|None = None



class AnswerBase(BaseModel):
    work_id:     uuid.UUID
    exercise_id: uuid.UUID
    file_keys:   list[str] | None = None  # Ключи файлов из хранилища
    text:        str

class AnswerRead(AnswerBase):
    id:          uuid.UUID
    assessments:  list[AssessmentRead]
    comments: list[CommentRead]

    model_config = {
        "from_attributes": True,
    }

class AnswerUpdate(AnswerBase):
    id:          uuid.UUID|None = None
    assessments: list[AssessmentUpdate]


class WorkBase(BaseModel):
    task_id:     uuid.UUID
    student_id:  uuid.UUID
    finish_date: datetime|None = None
    status:      StatusWork

class WorkRead(WorkBase):
    id: uuid.UUID
    answers: list[AnswerRead]

    model_config = {
        "from_attributes": True,
    }

class DetailWorkTeacher(BaseModelConfig):
    task: TaskRead
    work: WorkRead

class WorkUpdate(WorkRead):
    answers: list[AnswerUpdate]

class WorkEasyRead(BaseModel):
    id: uuid.UUID
    task_name: str
    subject: str
    student_name: str
    score: int
    max_score: int
    percent: int
    status_work: StatusWork

    model_config = {
        "from_attributes": True,
    }



from typing import List, Optional
from datetime import datetime

class SmartFiltersWorkTeacher(BaseModelConfig):
    students_ids: Optional[List[uuid.UUID]] = Field(Query(None))
    classrooms_ids: Optional[List[uuid.UUID]] = Field(Query(None))
    statuses: Optional[List[str]] = Field(Query(None))
    tasks_ids: Optional[List[uuid.UUID]] = Field(Query(None))
    subject_id: Optional[uuid.UUID] = None

    min: Optional[datetime] = None
    max: Optional[datetime] = None


class SmartFiltersWorkStudent(BaseModelConfig):
    teachers_ids: Optional[List[uuid.UUID]] = Field(Query(None))
    classrooms_ids: Optional[List[uuid.UUID]] = Field(Query(None))
    statuses: Optional[List[str]] = Field(Query(None))
    tasks_ids: Optional[List[uuid.UUID]] = Field(Query(None))
    subject_id: Optional[uuid.UUID] = None

    min: Optional[datetime] = None
    max: Optional[datetime] = None


