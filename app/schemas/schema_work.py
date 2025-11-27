

from datetime import datetime
import uuid
from pydantic import BaseModel

from app.models.model_works import StatusWork
from app.schemas.schema_comment import CommentRead
from app.schemas.schema_files import FileSchema


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
    files:       list[FileSchema]

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

class WorkUpdate(WorkRead):
    answers: list[AnswerUpdate]

class WorkEasyRead(BaseModel):
    id: uuid.UUID
    task_name: str
    student_name: str
    score: int
    max_score: int
    percent: int
    status_work: StatusWork

    model_config = {
        "from_attributes": True,
    }
