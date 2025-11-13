from fastapi import HTTPException, status
import uuid
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.responses import ErrorNotExists, ErrorPermissionDenied, ErrorRolePermissionDenied, Success
from app.models.model_comments import Comments
from app.models.model_files import Files
from app.models.model_tasks import Exercises, Tasks
from app.models.model_users import  RoleUser, Users, teachers_students
from app.models.model_works import Assessments, Answers, StatusWork, Works
from app.repositories.repo_task import RepoTasks
from app.schemas.schema_files import FileSchema
from app.schemas.schema_tasks import SchemaTask
from app.schemas.schema_work import WorkAllFilters, WorkEasyRead, WorkRead, WorkUpdate
from app.utils.logger import logger
from pydantic import BaseModel

from app.repositories.repo_work import RepoWorks
from app.services.service_base import ServiceBase





class ServiceWork(ServiceBase):


    async def create_works(
        self,
        task_id: uuid.UUID,
        teacher: Users,
        students_ids: list[uuid.UUID],
        classrooms_ids: list[uuid.UUID],
    ):
        try:            
            if len(students_ids) == 0 and len(classrooms_ids) == 0:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Add students or classes")

            if teacher.role is RoleUser.student:
                raise ErrorRolePermissionDenied(RoleUser.teacher, RoleUser.student)

            repo = RepoTasks(self.session)
            task_db = await repo.get(task_id)

            if task_db is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

            task = SchemaTask.model_validate(task_db)
            if task.teacher_id != teacher.id:
                raise ErrorPermissionDenied()

            students_ids = await get_students_from_classrooms(self.session, teacher, students_ids, classrooms_ids)

            await repo.create_works(task, students_ids)
            await self.session.commit()

            return JSONResponse(
                content={"status": "ok"},
                status_code=status.HTTP_201_CREATED
            )

        except HTTPException:
            raise

        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")  


    async def get(self, id: uuid.UUID):
        try:
            stmt = (
                select(Works)
                .where(Works.id == id)
                .options(
                    selectinload(Works.answers)
                    .selectinload(Answers.assessments),
                    selectinload(Works.answers)
                    .selectinload(Answers.files),
                    selectinload(Works.answers)
                    .selectinload(Answers.comments)
                    .selectinload(Comments.files)
                )
            )
            response = await self.session.execute(stmt)
            work_db = response.scalars().first()
            
            if work_db is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work not exists")
     
            stmt = (
                select(Tasks)
                .where(Tasks.id == work_db.task_id)
                .options(
                    selectinload(Tasks.exercises)
                    .selectinload(Exercises.criterions)
                )
            )
            response = await self.session.execute(stmt) 
            task_db = response.scalars().first()

            return JSONResponse(
                content={
                    "task": SchemaTask.model_validate(task_db).model_dump(mode="json"),
                    "work": WorkRead.model_validate(work_db).model_dump(mode="json")
                },
                status_code=status.HTTP_200_OK
            )

        except HTTPException as exc:
            raise

        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")


    async def get_all_teacher(
        self,
        user: Users,
        classrooms_ids: list[uuid.UUID]|None = None,
        students_ids: list[uuid.UUID]|None = None,
        subject_id: uuid.UUID | None = None,
        status_work: StatusWork | None = None
    ) -> list[WorkEasyRead]:
        try:
            if user.role is RoleUser.student and user.role is not RoleUser.admin:
                raise ErrorRolePermissionDenied(RoleUser.teacher, RoleUser.student)

            students_ids = await get_students_from_classrooms(self.session, user, students_ids, classrooms_ids)
            repo = RepoWorks(self.session)
            rows = await repo.get_all_teacher(
                user,
                students_ids,
                subject_id,
                status_work,
            )

            return rows_to_easy_read(rows)
            
        except HTTPException as exc:
            raise
        
        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")


    async def get_all_student(
        self,
        user: Users,
        subject_id: uuid.UUID | None = None,
        status_work: StatusWork | None = None
    ) -> list[WorkEasyRead]:
        try:
            if user.role is RoleUser.teacher and user.role is not RoleUser.admin:
                raise ErrorRolePermissionDenied(RoleUser.student, RoleUser.teacher)

            repo = RepoWorks(self.session)
            rows = await repo.get_all_student(user, subject_id, status_work)

            return rows_to_easy_read(rows)
            
        except HTTPException as exc:
            raise
        
        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")



# draft        = "draft" -- изначально
# inProgress   = "inProgress" -- после того как студент открыл
# verification = "verification" -- после того как студент отправил
# verificated  = "verificated" -- после того как учитель проверил
# canceled     = "canceled" -- после того как учитель отменил задание

    async def update(
        self,
        work_id: uuid.UUID,
        status: StatusWork,
        conclusion: str | None,
        user: Users
    ):
        try:
            # Получаем работу с загрузкой связанной задачи (для проверки teacher_id)
            work_db = await self.session.get(
                Works,
                work_id,
                options=[selectinload(Works.task)]
            )
            
            if not work_db:
                raise ErrorNotExists(Works)
            
            # Словарь приоритетов статусов
            work_status_weight = {
                "draft": 0,
                "inProgress": 1,
                "verification": 2,
                "verificated": 3,
                "canceled": 4,
            }
            
            current_weight = work_status_weight[work_db.status.value]
            new_weight = work_status_weight[status.value]
            

            # Проверка: статус можно только повышать (или оставлять текущий)
            if new_weight < current_weight:
                raise HTTPException(
                    status_code=400,
                    detail="Status can only be increased or kept the same, not decreased"
                )

            if user.role == RoleUser.student:
                # Ученик может:
                # - переводить из draft → inProgress
                # - переводить из inProgress → verification
                # - НЕ может устанавливать conclusion
                if current_weight > 1:
                    raise HTTPException(
                        status_code=403,
                        detail="Student cannot update work with status beyond 'inProgress'"
                    )
                
                if new_weight not in (1, 2):  # только inProgress или verification
                    raise HTTPException(
                        status_code=400,
                        detail="Student can only set status to 'inProgress' or 'verification'"
                    )
                    
                if conclusion is not None:
                    raise HTTPException(
                        status_code=400,
                        detail="Student cannot set conclusion"
                    )

            elif user.role == RoleUser.teacher:
                # Учитель может:
                # - переводить из verification → verificated
                # - переводить в canceled из любого статуса
                # - устанавливать conclusion
                if (new_weight == 3 and current_weight != 2):  # verificated только после verification
                    raise HTTPException(
                        status_code=400,
                        detail="Teacher can set 'verificated' only after 'verification'"
                    )
                    
                if new_weight == 4:  # canceled можно из любого статуса
                    pass  # разрешено

            else:
                raise HTTPException(status_code=403, detail="Unauthorized role")

            # Применяем изменения
            work_db.status = status
            if conclusion is not None:
                work_db.conclusion = conclusion


            await self.session.commit()
            return Success()

        except HTTPException:
            await self.session.rollback()
            raise

        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")


def rows_to_easy_read(rows):
    work_list = []
    for row in rows:
        # Распаковка результата и расчет процента
        score = row.score if row.score is not None else 0
        max_score = row.max_score if row.max_score is not None and row.max_score > 0 else 1 # Избегаем деления на ноль

        percent = round((score / max_score) * 100)
        
        work_list.append(
            WorkEasyRead(
                id=row.id,
                student_name=row.student_name,
                task_name=row.task_name,
                score=score,
                max_score=row.max_score,
                percent=percent,
                status_work=row.status_work
            )
        )
    return work_list


async def get_students_from_classrooms(
    session: AsyncSession,
    teacher: Users,
    students_ids: list[uuid.UUID]|None = None,
    classrooms_ids: list[uuid.UUID]|None = None,
) -> list[uuid.UUID]:


    if classrooms_ids is not None:
        if students_ids is None:
            students_ids = []

        stmt = (
            select(Users.id)
            .select_from(teachers_students)
            .join(Users, teachers_students.c.student_id == Users.id)
            .where(teachers_students.c.teacher_id == teacher.id)
            .where(teachers_students.c.classroom_id.in_(classrooms_ids))
        )

        response = await session.execute(stmt)
        ids_from_classroom = response.scalars().all()

        for id in ids_from_classroom:
            if id not in students_ids:
                students_ids.append(id)

    return students_ids