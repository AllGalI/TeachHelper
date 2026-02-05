

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload, load_only

from app.models.model_classroom import Classrooms
from app.models.model_users import Users, teachers_students, RoleUser
from app.schemas.schema_students import FilterStudents


class RepoClassroom():
    def __init__(self, session):
        self.session = session

    async def get_teacher_classrooms(self, filters: FilterStudents | None, teacher_id: uuid.UUID):
        # Загружаем классы с студентами через relationship
        stmt = (
            select(Classrooms)
            .where(Classrooms.teacher_id == teacher_id)
            .options(
                selectinload(Classrooms.students).load_only(Users.id, Users.first_name, Users.last_name)
            )
        )

        if filters and filters.classroom_id is not None:
            stmt = stmt.where(Classrooms.id == filters.classroom_id)

        result = await self.session.execute(stmt)
        classrooms = result.scalars().all()
        
        # Преобразуем в формат схемы ClassroomRead
        # Фильтруем студентов по роли (relationship уже фильтрует по classroom_id)
        classrooms_data = []
        for classroom in classrooms:
            students_list = [
                {
                    "id": student.id,
                    "name": f"{student.first_name} {student.last_name}"
                }
                for student in classroom.students
            ]
            classrooms_data.append({
                "id": classroom.id,
                "name": classroom.name,
                "students": students_list
            })
        
        return classrooms_data
