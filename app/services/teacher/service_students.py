import uuid
from fastapi import status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_users import RoleUser, Users
from app.repositories.repo_classrooms import RepoClassroom
from app.repositories.repo_user import RepoUser
from app.repositories.teacher.repo_students import RepoStudents

from app.exceptions.responses import ErrorRolePermissionDenied
from app.schemas.schema_students import (
    FilterStudents,
    StudentsPageResponse, 
    StudentsReadSchemaTeacher,
    StudentFilterItem,
    ClassroomFilterItem
)
from app.utils.logger import logger
from app.services.service_base import ServiceBase



class ServiceStudents(ServiceBase):

    async def get_all(self, filters: FilterStudents | None, teacher: Users):
        if teacher.role != RoleUser.teacher:
            raise ErrorRolePermissionDenied(RoleUser.teacher)


        students_repo = RepoStudents(self.session)

        students = await students_repo.get_single_students(filters, teacher)

        classrooms_repo = RepoClassroom(self.session)

        classrooms = await classrooms_repo.get_teacher_classrooms(filters, teacher.id)

        return StudentsPageResponse(
          classrooms=classrooms,
          single_students=students
        )



    async def get_performans_data(self, student_id: uuid.UUID, user: Users):
        if user.role != RoleUser.teacher:
            raise ErrorRolePermissionDenied(RoleUser.teacher)

        repo = RepoStudents(self.session)
        if not await repo.exists(user.id, student_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Студент не найден"
            )
        return await repo.get_performans_data(student_id)
        

    async def move_to_class(
        self,
        student_id: uuid.UUID,
        classroom_id: uuid.UUID,
        user: Users
    ):
        try:
            if user.role != RoleUser.teacher:
                raise ErrorRolePermissionDenied(RoleUser.teacher)
            
            repo = RepoStudents(self.session)

            if await repo.user_exists_in_class(user.id, student_id, classroom_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Студент уже находится в этом классе"
                )
            await repo.move_to_class(user.id, student_id, classroom_id)
            await self.session.commit()
            return JSONResponse(content={"status": "ok"}, status_code=status.HTTP_200_OK)
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Ошибка при перемещении ученика в класс")
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def remove_from_class(
        self,
        student_id: uuid.UUID,
        classroom_id: uuid.UUID,
        user: Users
    ):
        repo = RepoStudents(self.session)
        try:
            if user.role != RoleUser.teacher:
                raise ErrorRolePermissionDenied(RoleUser.teacher)
            
            if not await repo.exists(user.id, student_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Студент не найден"
                )
            if not await repo.user_exists_in_class(user.id, student_id, classroom_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Студент не состоит в этом классе"
                )
            await repo.remove_from_class(user.id, student_id, )
            await self.session.commit()
            return JSONResponse(content={"status": "ok"}, status_code=status.HTTP_200_OK)
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Ошибка при удалении ученика из класса")
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def delete(
        self,
        student_id: uuid.UUID,
        user: Users
    ):
        try:
            if user.role != RoleUser.teacher:
                raise ErrorRolePermissionDenied(RoleUser.teacher)
            
            repo = RepoStudents(self.session)
            if not await repo.exists(user.id, student_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Студент не найден"
                )
            await repo.delete(teacher_id=user.id, student_id=student_id)
            await self.session.commit()
            return JSONResponse(content={"status": "ok"}, status_code=status.HTTP_200_OK)
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Ошибка при удалении ученика")
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def add_teacher(self, teacher_id: uuid.UUID, student: Users):
        if student.role != RoleUser.student:
            raise ErrorRolePermissionDenied(RoleUser.student)

        repo_user = RepoUser(self.session)
        if await repo_user.get(teacher_id) is  None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Teacher is not exists")

        repo = RepoStudents(self.session)
        await repo.add_teacher(teacher_id, student.id)
        await self.session.commit()
        return JSONResponse(
            {"status": "ok"},
            status.HTTP_201_CREATED
        )

    async def get_filters(self, user: Users) -> StudentsReadSchemaTeacher:
        """
        Получение доступных фильтров для учителя: список студентов и классов
        """
        if user.role != RoleUser.teacher:
            raise ErrorRolePermissionDenied(RoleUser.teacher)

        repo = RepoStudents(self.session)
        rows = await repo.get_filters(user.id)

        # Формируем ответ с уникальными значениями
        students_set = set()
        classrooms_set = set()

        for row in rows:
            # Добавляем студентов (id, name) в set для уникальности
            if row["student_id"]:
                students_set.add((row["student_id"], row["student_name"]))
            
            # Добавляем классы (id, name) в set для уникальности
            if row["classroom_id"]:
                classrooms_set.add((row["classroom_id"], row["classroom_name"]))

        # Преобразуем sets в списки объектов схемы
        students_list = [
            StudentFilterItem(id=item[0], name=item[1]) 
            for item in students_set
        ]
        classrooms_list = [
            ClassroomFilterItem(id=item[0], name=item[1]) 
            for item in classrooms_set
        ]

        # Возвращаем схему с валидированными данными
        return StudentsReadSchemaTeacher(
            students=students_list,
            classrooms=classrooms_list
        )
        
            