

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload, load_only

from app.models.model_classroom import Classrooms
from app.models.model_users import Users, teachers_students


class RepoClassroom():
    def __init__(self, session):
        self.session = session

    async def get_teacher_classrooms(self, teacher_id: uuid.UUID):
        stmt = (
            select(
                Classrooms.id,
                Classrooms.name
            )
            .where(Classrooms.teacher_id == teacher_id)
        )
        result = await self.session.execute(stmt)
        return result.mappings().all()
