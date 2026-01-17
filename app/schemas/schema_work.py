

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



from typing import List, Optional, Dict
from datetime import datetime, date

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


# Схемы для WorksFilterResponseTeacher
class StudentItem(BaseModelConfig):
    """Модель для представления студента в фильтрах"""
    id: uuid.UUID  # student_id
    name: str  # student_name


class ClassroomItem(BaseModelConfig):
    """Модель для представления класса в фильтрах"""
    id: uuid.UUID  # classroom_id
    name: str  # classroom_name


class SubjectItem(BaseModelConfig):
    """Модель для представления предмета в фильтрах"""
    id: uuid.UUID  # subject_id
    name: str  # subject


class DatesRange(BaseModelConfig):
    """Модель для диапазона дат в фильтрах"""
    min: Optional[date] = None  # Минимальная дата
    max: Optional[date] = None  # Максимальная дата


class WorksFilterResponseTeacher(BaseModelConfig):
    """Схема ответа для фильтров работ учителя"""
    students: List[StudentItem]  # Список студентов (id, name)
    classrooms: List[ClassroomItem]  # Список классов (id, name)
    statuses: List[str]  # Список статусов работ
    dates: Optional[DatesRange] = None  # Диапазон дат (min, max) или None
    tasks: Dict[str, List[uuid.UUID]]  # Словарь: название задачи -> список ID задач
    subjects: List[SubjectItem]  # Список предметов (id, name)

