import uuid
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_classroom import Classrooms
from app.repositories.repo_classrooms import RepoClassroom
from app.repositories.repo_teacher import RepoTeacher
from app.utils.logger import logger
from app.services.service_base import ServiceBase

class ServiceClassroom(ServiceBase):


    async def create(self, name: str, teacher):
        try:
            response = await self.session.execute(
                select(Classrooms)
                .where(Classrooms.teacher_id == teacher.id)
                .where(Classrooms.name == name)
            )

            classroom_db = response.scalar_one_or_none()
            if classroom_db is not None:
                raise HTTPException(status_code=409, detail="Classroom with this name already exists")

            classroom = Classrooms(
                name=name,
                teacher_id=teacher.id
            )

            self.session.add(classroom)
            await self.session.commit()
            return classroom
        except HTTPException:
            raise

        except Exception as exc:
            logger.exception(exc)
            raise
        finally:
            await self.session.rollback()



    async def get_all(self, teacher):
        repo = RepoTeacher(self.session)
        return await repo.get_classrooms(teacher)


    # async def get(self, id: uuid.UUID, teacher):
    #     repo = RepoClassroom(self.session)
    #     if not await repo.exists(id):
    #         raise HTTPException(status.HTTP_404_NOT_FOUND, "This classroom doesn't exists")

    #     return await repo.get_students(id, teacher.id)


    async def update(self, id: uuid.UUID, name: str):
        repo = RepoClassroom(self.session)
        classroom = await self.session.get(Classrooms, id)
        if classroom is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "This classroom doesn't exists")

        classroom.name = name
        await self.session.commit()
        return {"message": "success"}


    async def delete(self, id: uuid.UUID):
        classroom = await self.session.get(Classrooms, id)
        if classroom is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "This classroom doesn't exists")

        await self.session.delete(classroom)
        await self.session.commit()
        return {"message": "success"}


        
    
        
        
    # async def get_performans_data(self, student_id: uuid.UUID, user: Users):
    #     if user.role != RoleUser.teacher:
    #         raise ErrorRolePermissionDenied(RoleUser.teacher)

    #     repo = RepoStudents(self.session)
    #     if not await repo.exists(user.id, student_id):
    #         raise HTTPException(
    #             status_code=status.HTTP_404_NOT_FOUND,
    #             detail="Студент не найден"
    #         )
    #     results = await repo.get_performans_data(student_id)
        
    #     students = {}
    #     for s in results["agg_data"]:
    #         student_id = s["student_id"]
    #         students[student_id] = dict(s)
    #         students[student_id]["works"] = []


    #     for row in results["works_data"]:
    #         student_id = row["student_id"]
    #         if student_id in students:
    #             students[student_id]["works"].append({
    #                 "submission_id": row["submission_id"],
    #                 "status": row["status"],
    #                 "total_score": row["total_score"],
    #                 "task_title": row["task_title"],
    #                 "score": row["score"]
    #             })

    #     return students.values()