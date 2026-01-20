from typing import Optional
import uuid
from pydantic import BaseModel

from app.models.model_works import StatusWork
from app.services.schema_base import BaseModelConfig



class SchemaStudentPerfomansWorks(BaseModel):
    submission_id: uuid.UUID
    status: StatusWork
    total_score: int
    task_title: str
    score: int

class SchemaStudentPerformans(BaseModel):
    student_id: uuid.UUID
    student_name: str
    verificated_works_count: int
    avg_score: int
    works: list[SchemaStudentPerfomansWorks]



class StudentRead(BaseModelConfig):
    id: uuid.UUID
    name: str
    classroom: Optional[uuid.UUID] = None

class ClassroomRead(BaseModelConfig):
    id: uuid.UUID
    name: str

class UsersPageSchema(BaseModelConfig):
    students: list[StudentRead]
    classrooms: list[ClassroomRead]


class StudentFilterItem(BaseModelConfig):
    """Элемент фильтра студента: id и имя"""
    id: uuid.UUID
    name: str


class ClassroomFilterItem(BaseModelConfig):
    """Элемент фильтра класса: id и имя"""
    id: uuid.UUID
    name: str


class StudentsReadSchemaTeacher(BaseModelConfig):
    """Схема для получения фильтров студентов для учителя"""
    students: list[StudentFilterItem]
    classrooms: list[ClassroomFilterItem]
    