import asyncio
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from app.services.schema_base import BaseModelConfig
from app.schemas.schema_files import IFile

class TasksListItem(BaseModel):
    id: uuid.UUID
    name: str
    subject_id: uuid.UUID
    subject: str
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174001",
                "name": "Задача по математике",
                "subject_id": "b1697c3a-5486-4bea-8aed-4e2552be92f3",
                "subject": "Математика",
                "updated_at": "2023-10-26T12:00:00"
            }
        }
    }


class TasksFilters(BaseModel):
    task_id: uuid.UUID|None = None
    subject_id: uuid.UUID|None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Математика",
                "subject_id": "b1697c3a-5486-4bea-8aed-4e2552be92f3"
            }
        }
    }


class SubjectFilterItem(BaseModelConfig):
    """Элемент фильтра предмета: id и имя"""
    id: uuid.UUID
    name: str


class TaskFilterItem(BaseModelConfig):
    """Элемент фильтра задачи: id и имя"""
    id: uuid.UUID
    name: str


class TasksFiltersReadSchema(BaseModelConfig):
    """Схема для получения фильтров задач для учителя"""
    subjects: list[SubjectFilterItem]
    tasks: list[TaskFilterItem]



# create
class CriterionCreate(BaseModel):
    name: str
    score: int

class ExerciseCreate(BaseModel):
    name: str
    description: str
    order_index: int
    criterions: list[CriterionCreate]
    files: list[str]  # Список ID файлов


class TaskCreate(BaseModel):
    subject_id: uuid.UUID
    name: str|None = None
    description: str|None = None
    deadline:    datetime|None = None
    exercises: list[ExerciseCreate] = Field(min_length=1)


# Update
class CriterionUpdate(BaseModelConfig):
    id:          uuid.UUID|None = None
    name:        str
    score:       int
    exercise_id: uuid.UUID


class ExerciseUpdate(BaseModelConfig):
    id:          uuid.UUID|None = None
    name:        str        
    description: str            
    order_index: int            
    task_id:     uuid.UUID
    criterions:  list[CriterionUpdate]
    files:       list[str]


class TaskUpdate(BaseModelConfig):
    id:          uuid.UUID
    name:        str
    description: str
    deadline:   datetime|None = None
    subject_id: uuid.UUID
    teacher_id: uuid.UUID
    updated_at: datetime|None = None
    created_at: datetime|None = None
    exercises:   list[ExerciseUpdate]


# Read

class CriterionRead(BaseModelConfig):
    id:          uuid.UUID
    name:        str
    score:       int
    exercise_id: uuid.UUID


class ExerciseRead(BaseModelConfig):
    id:          uuid.UUID
    name:        str        
    description: str            
    order_index: int            
    task_id:     uuid.UUID
    criterions:  list[CriterionUpdate]
    files:       list[IFile]





class TaskRead(BaseModelConfig):
    id:          uuid.UUID
    name:        str
    description: str
    deadline:   datetime|None = None
    subject_id: uuid.UUID
    teacher_id: uuid.UUID
    updated_at: datetime|None = None
    created_at: datetime|None = None
    exercises: list[ExerciseRead]


__all__ = [
    "TasksListItem",
    "TasksFilters",
    "TaskFilterItem",
    "SubjectFilterItem",
    "TasksFiltersReadSchema",

    "CriterionCreate",
    "ExerciseCreate",
    "TaskCreate",

    "CriterionUpdate",
    "ExerciseUpdate",
    "TaskUpdate",

    "CriterionRead",
    "ExerciseRead",
    "TaskRead"
]