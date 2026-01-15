import asyncio
import uuid

from fastapi import HTTPException, status, Response
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import  joinedload, selectinload, Load

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.repo_task import RepoTasks
from app.schemas.schema_tasks import *
from app.models.model_tasks import  Criterions, Exercises, Tasks
from app.schemas.schema_files import IFile, compare_lists
from app.config.boto import delete_files_from_s3, get_presigned_url

from app.models.model_users import RoleUser, Users
from app.utils.logger import logger
from app.services.service_base import ServiceBase

class ServiceTasks(ServiceBase):

    async def create(self, teacher: Users, data: TaskCreate) -> TaskRead:
        try:
            if teacher.role is RoleUser.student:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User don't have permission to delete this task")

            # Создаем задачу, исключая вложенные структуры (exercises)
            task_dict = data.model_dump(exclude={"exercises"})
            task = Tasks(teacher_id=teacher.id, **task_dict)

            # Создаем вложенные объекты Exercises и Criterions
            exercises_orm = []
            for exercise_data in data.exercises:
                # Создаем критерии для каждого упражнения
                criterions_orm = [
                    Criterions(**criterion.model_dump())
                    for criterion in exercise_data.criterions
                ]

                # Создаем упражнение, исключая criterions (они обрабатываются отдельно)
                exercise_dict = exercise_data.model_dump(exclude={"criterions"})
                exercise_orm = Exercises(**exercise_dict)
                # Присваиваем критерии и файлы упражнению
                exercise_orm.criterions = criterions_orm
                exercises_orm.append(exercise_orm)

            # Присваиваем упражнения задаче
            task.exercises = exercises_orm

            self.session.add(task)
            await self.session.flush()  # Получаем ID задачи и упражнений
            await self.session.commit()
            task_read = await orm_to_task_read(task)

            return JSONResponse(
                content=task_read.model_dump(mode='json'),
                status_code=status.HTTP_201_CREATED
            )

        except HTTPException as exc:
            await self.session.rollback()
            raise

        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")


    async def get_all(self, teacher: Users, filters: TasksFilters) -> list[TasksListItem]:
        try:
            if teacher.role is RoleUser.student:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User don't have permission to delete this task")

            # Используем репозиторий для получения задач
            repo = RepoTasks(self.session)
            tasks = await repo.get_all(teacher.id, filters)
            return [TasksListItem.model_validate(task) for task in tasks]
    
        except HTTPException as exc:
            raise

        except Exception as exc:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")


    async def get(self, id: uuid.UUID, teacher: Users) -> TaskRead:
        try:
            if teacher.role is RoleUser.student:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User don't have permission to delete this task")

            # Загружаем задачу с файлами через selectinload
            stmt = (
                select(Tasks)
                .where(Tasks.id == id)
                .options(
                    selectinload(Tasks.exercises).selectinload(Exercises.criterions),

                )
            )
            result = await self.session.execute(stmt)
            task = result.scalar_one_or_none()
            
            if not task: 
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

            task_read = await orm_to_task_read(task)

            # Возвращаем JSON
            return task_read.model_dump(mode="json")

        except HTTPException as exc:
            raise

        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")


    async def update(self, id: uuid.UUID, update_data: TaskUpdate, teacher: Users) -> TaskRead:
        try:
            print(teacher.__dict__)
            if teacher.role is RoleUser.student:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User don't have permission to delete this task")

            stmt = (
                select(Tasks)
                .where(Tasks.id == id)
                .options(
                    selectinload(Tasks.exercises).selectinload(Exercises.criterions),

                )
            )
            result = await self.session.execute(stmt)
            task_db = result.scalar_one_or_none()
            
            if not task_db: 
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

            exercises_orm = []
            files_to_delete = []

            exercise_files = {}

            for ex_db in task_db.exercises:
              exercise_files[ex_db.id] = ex_db.files

            for exercise_data in update_data.exercises:
                criterions_orm = [
                    Criterions(**criterion.model_dump())
                    for criterion in exercise_data.criterions
                ]

                files_to_delete.extend(compare_lists(exercise_files[exercise_data.id], exercise_data.files)['removed'])

                exercise_dict = exercise_data.model_dump(exclude={"criterions"})
                exercise_orm = Exercises(**exercise_dict)
                exercise_orm.criterions = criterions_orm

            exercises_orm.append(exercise_orm)

            task_dict = update_data.model_dump(exclude={"exercises"})
            task_orm = Tasks(**task_dict)
            task_orm.exercises = exercises_orm

            await self.session.merge(task_orm)
            await delete_files_from_s3(files_to_delete)
            await self.session.commit()

            task_read = await orm_to_task_read(task_orm)
            # Возвращаем JSON
            return task_read.model_dump(mode="json")


        except HTTPException:
            raise

        except Exception as exc:
            logger.exception(exc)
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR)


    async def delete(self, id: uuid.UUID, teacher: Users) -> JSONResponse:
        try:
            if teacher.role is RoleUser.student:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User don't have permission to delete this task")

            # Загружаем задачу с упражнениями и файлами для получения всех ключей файлов
            stmt = (
                select(Tasks)
                .where(Tasks.id == id)
                .options(
                    selectinload(Tasks.exercises).selectinload(Exercises.criterions),
                )
            )
            result = await self.session.execute(stmt)
            task = result.scalar_one_or_none()
            
            if task is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

            if task.teacher_id != teacher.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User don't have permission to delete this task")

            # Собираем все ключи файлов для удаления из S3
            file_keys_to_delete = []
            
            # Добавляем ключи изображений задачи, если они есть

            # Добавляем ключи файлов из всех упражнений через связи Files
            if task.exercises:
                for exercise in task.exercises:
                    file_keys_to_delete.extend(exercise.files)

            # Удаляем файлы из S3, если есть ключи для удаления
            if file_keys_to_delete:
                try:
                    await delete_files_from_s3(file_keys_to_delete)
                except Exception as s3_exc:
                    # Логируем ошибку, но продолжаем удаление задачи из БД
                    logger.warning(f"Failed to delete files from S3: {s3_exc}")

            # Удаляем задачу из БД (каскадно удалятся упражнения и критерии)
            await self.session.delete(task)
            await self.session.commit()

            return JSONResponse(
                content={"status": "ok"},
                status_code=status.HTTP_200_OK
            )

        except HTTPException:
            raise

        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def get_filters(self, teacher: Users) -> TasksFiltersReadSchema:
        """
        Получение доступных фильтров для учителя: список предметов и задач
        """
        if teacher.role is RoleUser.student:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="User don't have permission to get filters"
            )

        repo = RepoTasks(self.session)
        rows = await repo.get_filters(teacher.id)

        # Преобразуем данные в объекты схемы
        subjects_list = [
            SubjectFilterItem(id=row["subject_id"], name=row["subject_name"])
            for row in rows["subjects"]
        ]
        tasks_list = [
            TaskFilterItem(id=row["task_id"], name=row["task_name"])
            for row in rows["tasks"]
        ]

        # Возвращаем схему с валидированными данными
        return TasksFiltersReadSchema(
            subjects=subjects_list,
            tasks=tasks_list
        )

async def orm_to_exercise_read(exercise_orm: Exercises) -> ExerciseRead:
    # Получаем presigned URLs для файлов
    files: list[IFile] = []
    if exercise_orm.files:
        for key in exercise_orm.files:
            try:
                presigned_url = await get_presigned_url(key)
                files.append(IFile(key=key, file=presigned_url))
            except Exception as exc:
                logger.warning(f"Failed to get presigned URL for file {key}: {exc}")

    # Преобразуем Criterions → CriterionRead
    criterions: list[CriterionRead] = [
        CriterionRead(
            id=crit.id,
            name=crit.name,
            score=crit.score,
            exercise_id=crit.exercise_id
        )
        for crit in exercise_orm.criterions
    ]

    return ExerciseRead(
        id=exercise_orm.id,
        name=exercise_orm.name,
        description=exercise_orm.description,
        order_index=exercise_orm.order_index,
        task_id=exercise_orm.task_id,
        criterions=criterions,
        files=files
    )

async def orm_to_task_read(task_orm: Tasks) -> TaskRead:
    # Асинхронно преобразуем все упражнения
    exercises: list[ExerciseRead] = await asyncio.gather(
        *[orm_to_exercise_read(ex) for ex in task_orm.exercises]
    )

    return TaskRead(
        id=task_orm.id,
        name=task_orm.name,
        description=task_orm.description,
        deadline=task_orm.deadline,
        subject_id=task_orm.subject_id,
        teacher_id=task_orm.teacher_id,
        updated_at=task_orm.updated_at,
        created_at=task_orm.created_at,
        exercises=exercises
    )

