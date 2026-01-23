

from datetime import datetime
import uuid
from fastapi import Query
from pydantic import BaseModel, Field

from typing import List, Optional, Dict
from datetime import datetime, date

from app.models.model_works import StatusWork
from app.schemas.schema_base import BaseModelConfig
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.schema_comment import CommentRead
    from app.schemas.schema_files import IFile


class WorkAllFilters(BaseModel):
    subject_id: uuid.UUID|None = None
    students_ids: list[uuid.UUID]|None = None
    classrooms_ids: list[uuid.UUID]|None = None
    status_work: StatusWork|None = None


class CriterionRead(BaseModelConfig):
    id: uuid.UUID
    name: str
    score: int

class ExerciseRead(BaseModelConfig):
    id: uuid.UUID
    task_id: uuid.UUID
    name: str
    description: str
    order_index: int
    files: list["IFile"]

class TaskRead(BaseModelConfig):
    id: uuid.UUID
    name: str
    description: str
    deadline: str | None
    subject_id: uuid.UUID


class AssessmentRead(BaseModelConfig):
    id: uuid.UUID
    answer_id: uuid.UUID
    criterion_id: uuid.UUID
    points: int
    criterion: list[CriterionRead]  # CriterionRead определен в том же файле


class AnswerRead(BaseModelConfig):
    id: uuid.UUID
    work_id: uuid.UUID
    exercise_id: uuid.UUID
    text: str
    general_comment: str
    files: list["IFile"]  # IFile из другого модуля

    exercise: ExerciseRead  # ExerciseRead определен в том же файле
    assessments: list[AssessmentRead]  # AssessmentRead определен в том же файле
    comments: list["CommentRead"]  # CommentRead из другого модуля


class WorkRead(BaseModelConfig):
    id: uuid.UUID
    task_id: uuid.UUID
    student_id: uuid.UUID
    finish_date: datetime | None
    status: StatusWork
    conclusion: str
    ai_verificated: bool

    task: TaskRead  # TaskRead определен в том же файле
    answers: list[AnswerRead]  # AnswerRead определен в том же файле


class AssessmentUpdate(BaseModelConfig):
    id: uuid.UUID | None = None
    answer_id: uuid.UUID | None = None
    criterion_id: uuid.UUID | None = None
    points: int


class AnswerUpdate(BaseModelConfig):
    id: uuid.UUID | None = None
    work_id: uuid.UUID | None = None
    exercise_id: uuid.UUID | None = None
    text: str
    general_comment: str
    files: list[str]  # IFile из другого модуля

    assessments: list[AssessmentUpdate]  # AssessmentUpdate определен в том же файле

class WorkUpdate(BaseModelConfig):
    id: uuid.UUID
    task_id: uuid.UUID
    student_id: uuid.UUID
    finish_date: datetime | None = None
    status: StatusWork
    conclusion: str
    ai_verificated: bool

    answers: list[AnswerUpdate]  # AnswerUpdate определен в том же файле


class WorkEasyRead(BaseModelConfig):
    id: uuid.UUID
    task_name: str
    subject: str
    student_name: str
    score: int
    max_score: int
    percent: int
    status_work: StatusWork


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
    statuses: Optional[List[str]] = Field(Query(None))
    tasks_ids: Optional[List[uuid.UUID]] = Field(Query(None))
    subject_id: Optional[uuid.UUID] = None

    min: Optional[datetime] = None
    max: Optional[datetime] = None


# Схемы для WorksFilterResponseTeacher
class UserItem(BaseModelConfig):
    """Модель для представления студента в фильтрах"""
    id: uuid.UUID  # user_id
    name: str  # user_name


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
    students: List[UserItem]  # Список студентов (id, name)
    classrooms: List[ClassroomItem]  # Список классов (id, name)
    statuses: List[str]  # Список статусов работ
    dates: Optional[DatesRange] = None  # Диапазон дат (min, max) или None
    tasks: Dict[str, List[uuid.UUID]]  # Словарь: название задачи -> список ID задач
    subjects: List[SubjectItem]  # Список предметов (id, name)

class WorksFilterResponseStudent(BaseModelConfig):
    """Схема ответа для фильтров работ учителя"""
    teachers: List[UserItem]  # Список студентов (id, name)
    statuses: List[str]  # Список статусов работ
    dates: Optional[DatesRange] = None  # Диапазон дат (min, max) или None
    tasks: Dict[str, List[uuid.UUID]]  # Словарь: название задачи -> список ID задач
    subjects: List[SubjectItem]  # Список предметов (id, name)


# Вызов model_rebuild() для разрешения forward references
def _rebuild_models():
    """Пересборка моделей для разрешения строковых аннотаций"""
    from app.schemas.schema_comment import CommentRead
    from app.schemas.schema_files import IFile
    
    # Пересборка моделей, использующих классы из других модулей
    # Порядок важен: сначала модели, которые зависят только от внешних модулей,
    # затем модели, которые зависят от уже пересобранных моделей
    
    # Модели Read (используют IFile и CommentRead из других модулей)
    ExerciseRead.model_rebuild()  # использует IFile из другого модуля
    AnswerRead.model_rebuild()  # использует CommentRead и IFile из других модулей
    WorkRead.model_rebuild()  # использует AnswerRead и TaskRead
    
    # Модели Update (используют IFile из другого модуля)
    AnswerUpdate.model_rebuild()  # использует IFile из другого модуля и AssessmentUpdate
    WorkUpdate.model_rebuild()  # использует AnswerUpdate

_rebuild_models()
