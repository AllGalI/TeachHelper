from datetime import date
import string
import uuid
from fastapi import Query
from pydantic import BaseModel

from app.models.model_works import StatusWork
from app.schemas.schema_base import BaseModelConfig
from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class StudentRead(BaseModelConfig):
    id: uuid.UUID
    name: str

class ClassroomRead(BaseModelConfig):
    id: uuid.UUID
    name: str
    students: list[StudentRead]

class StudentsPageResponse(BaseModelConfig):
  classrooms: list[ClassroomRead]
  single_students: list[StudentRead]


class FilterStudents(BaseModelConfig):
  student_id: Optional[uuid.UUID] = None
  classroom_id: Optional[uuid.UUID] = None


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
    