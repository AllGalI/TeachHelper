from fastapi import HTTPException, status
import uuid
from fastapi.responses import JSONResponse
import pika
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.responses import ErrorNotExists, ErrorPermissionDenied, ErrorRolePermissionDenied, Success
from app.models.model_comments import Comments
from app.models.model_tasks import Tasks
from app.models.model_users import  RoleUser, Users, teachers_students
from app.models.model_works import Assessments, Answers, StatusWork, Works
from app.models.model_files import AnswerFiles, StatusAnswerFile
from app.repositories.repo_task import RepoTasks
from app.schemas.schema_comment import CommentRead, Coordinates as CoordinatesSchema
from app.schemas.schema_files import IFile, IFileAnswer, IFileAnserUpdate, compare_lists
from app.schemas.schema_work import AnswerUpdate, CriterionRead, ExerciseRead, TaskRead
from app.config.boto import delete_files_from_s3, get_presigned_url
from app.config.rabbit import WorkRequestDTO, channel
from app.schemas.schema_work import AnswerRead, AssessmentRead, SmartFiltersWorkStudent, SmartFiltersWorkTeacher, WorkEasyRead, WorkRead, WorkUpdate, WorksFilterResponseStudent, WorksFilterResponseTeacher
from app.utils.logger import logger
from app.transformers.transformer_work import TransformerWorks

from app.repositories.repo_work import RepoWorks
from app.services.service_base import ServiceBase

class ServiceWork(ServiceBase):

    async def get_smart_filters_teacher(self, user: Users, filters: SmartFiltersWorkTeacher) -> WorksFilterResponseTeacher:
        repo = RepoWorks(self.session)
        if user.role is RoleUser.student:
            raise ErrorRolePermissionDenied(RoleUser.teacher, user.role)

        rows = await repo.get_smart_filters_teacher(user.id, filters)
        return TransformerWorks.handle_filters_response(user, rows)


    async def get_smart_filters_student(self, user: Users, filters: SmartFiltersWorkStudent)-> WorksFilterResponseStudent:
        repo = RepoWorks(self.session)
        if user.role is RoleUser.teacher:
            raise ErrorRolePermissionDenied(RoleUser.student, user.role)

        rows = await repo.get_smart_filters_student(user.id, filters)
        return TransformerWorks.handle_filters_response(user, rows)

    async def get_works_list_teacher(
        self,
        user: Users,
        filters: SmartFiltersWorkTeacher
    ) -> list[WorkEasyRead]:
        """Получение списка работ для учителя с применением умных фильтров"""
        try:
            if user.role is RoleUser.student and user.role is not RoleUser.admin:
                raise ErrorRolePermissionDenied(RoleUser.teacher, user.role)

            repo = RepoWorks(self.session)
            rows = await repo.get_works_list_teacher(user.id, filters)
            return rows_to_easy_read(rows)

        except HTTPException as exc:
            raise
        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def get_works_list_student(
        self,
        user: Users,
        filters: SmartFiltersWorkStudent
    ) -> list[WorkEasyRead]:
        """Получение списка работ для ученика с применением умных фильтров"""
        try:
            if user.role is RoleUser.teacher and user.role is not RoleUser.admin:
                raise ErrorRolePermissionDenied(RoleUser.student, user.role)

            repo = RepoWorks(self.session)
            rows = await repo.get_works_list_student(user.id, filters)
            return rows_to_easy_read(rows)

        except HTTPException as exc:
            raise
        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")


    async def create_works(
        self,
        task_id: uuid.UUID,
        teacher: Users,
        students_ids: list[uuid.UUID] | None,
        classrooms_ids: list[uuid.UUID] | None,
    ):
        try:            
            if students_ids is None and classrooms_ids  is None:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Add students or classes")

            if teacher.role is RoleUser.student:
                raise ErrorRolePermissionDenied(RoleUser.teacher, RoleUser.student)

            repo = RepoTasks(self.session)
            task_db = await repo.get(task_id)

            if task_db is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

            if task_db.teacher_id != teacher.id:
                raise ErrorPermissionDenied()

            students_ids = await get_students_from_classrooms(self.session, teacher, students_ids, classrooms_ids)

            await repo.create_works(task_db, students_ids)
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


    async def get(self, work_id: uuid.UUID, user: Users) -> WorkRead:
        """Получение работы с проверкой прав доступа"""
        try:
            repo = RepoWorks(self.session)
            work_db = await repo.get(work_id)
            
            if work_db is None:
                raise ErrorNotExists(Works)
            
            # Проверка прав доступа: студент может видеть только свои работы, учитель - работы своих студентов
            if user.role is RoleUser.student:
                if work_db.student_id != user.id:
                    raise ErrorPermissionDenied()
            elif user.role is RoleUser.teacher:
                # Учитель может видеть только работы по своим задачам
                if work_db.task.teacher_id != user.id:
                    raise ErrorPermissionDenied()
            
            # Преобразуем ORM в схему
            work_read = await orm_to_work_read(work_db)
            return work_read
            
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def update(self, work_id: uuid.UUID, update_data: WorkUpdate, user: Users) -> WorkRead:
        """Обновление работы с проверкой прав доступа и ограничений по полям"""
        try:
            repo = RepoWorks(self.session)
            work_db = await repo.get(work_id)
            
            if work_db is None:
                raise ErrorNotExists(Works)
            
            # Проверка прав доступа
            if user.role is RoleUser.student:
                if work_db.student_id != user.id:
                    raise ErrorPermissionDenied()
            elif user.role is RoleUser.teacher:
                if work_db.task.teacher_id != user.id:
                    raise ErrorPermissionDenied()

            # Применяем изменения с учетом прав доступа
            await apply_work_updates(work_db, update_data, user, self.session)
            # Явно добавляем объект в сессию для отслеживания изменений
            # Это гарантирует, что SQLAlchemy отследит все изменения
            
            await self.session.commit()
            
            # Получаем обновленную работу
            work_db = await repo.get(work_id)
            work_read = await orm_to_work_read(work_db)
            return work_read
            
        except HTTPException:
            await self.session.rollback()
            raise
        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def send_work_to_verification(
        self,
        work_id: uuid.UUID,
        user: Users
    ):
        try:
            if user.role is RoleUser.student:
                raise ErrorRolePermissionDenied(RoleUser.teacher, user.role)

            stmt = (
                select(Works)
                .join(Tasks, Works.task_id == Tasks.id)
                .where(
                    Works.id == work_id,
                    Tasks.teacher_id == user.id
                )
                .options(
                    selectinload(Works.answers).load_only(Answers.id)
                )
            )


            result = await self.session.execute(stmt)
            work_db = result.scalars().first()
            
            if work_db is None:
                raise ErrorNotExists(Works)

            if work_db.ai_verificated:
                raise HTTPException(status.HTTP_409_CONFLICT, "This work already verificated by AI")

            if work_db.status is not StatusWork.verification:
                raise HTTPException(403, "Work must have verification status")

            channel.basic_publish(
                exchange='',
                routing_key='htr_queue',
                properties=pika.BasicProperties(
                    content_type="application/json",
                ),
                body=WorkRequestDTO.model_validate(work_db).model_dump_json().encode()
            )

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
                subject=row.subject,
                task_name=row.task_name,
                score=score,
                max_score=max_score,
                percent=percent,
                status_work=row.status
            )
        )
    return work_list



async def get_students_from_classrooms(
    session: AsyncSession,
    teacher: Users,
    student: uuid.UUID|None = None,
    classroom: uuid.UUID|None = None,
) -> list[uuid.UUID]:

    if student: 
      return student

    if classroom is not None:
        if student is None:
            student = []

        stmt = (
            select(Users.id)
            .select_from(teachers_students)
            .join(Users, teachers_students.c.student_id == Users.id)
            .where(teachers_students.c.teacher_id == teacher.id)
            .where(teachers_students.c.classroom_id == classroom)
        )
        
        if student is not None:
          stmt = stmt.where(teachers_students.c.student_id == student)

        response = await session.execute(stmt)
        ids_from_classroom = response.scalars().all()

    return ids_from_classroom


async def orm_to_assessment_read(assessment_orm: Assessments) -> AssessmentRead:
    """Преобразование Assessment ORM в AssessmentRead схему"""
    return AssessmentRead(
        id=assessment_orm.id,
        answer_id=assessment_orm.answer_id,
        criterion_id=assessment_orm.criterion_id,
        points=assessment_orm.points,
        criterion=[
            CriterionRead(
                id=assessment_orm.criterion.id,
                name=assessment_orm.criterion.name,
                score=assessment_orm.criterion.score
            )
        ] if assessment_orm.criterion else []
    )


async def orm_to_comment_read(comment_orm: Comments) -> CommentRead:
    """Преобразование Comment ORM в CommentRead схему"""
    # Получаем presigned URLs для файлов
    # В модели Comments поле называется 'files', а не 'file_keys'
    file_keys = comment_orm.files if comment_orm.files else []
    files = []
    if file_keys:
        for key in file_keys:
            try:
                presigned_url = await get_presigned_url(key)
                files.append(IFile(key=key, file=presigned_url))
            except Exception as exc:
                logger.warning(f"Failed to get presigned URL for file {key}: {exc}")
    
    # Преобразуем coordinates из ORM объектов в схему Coordinates
    # coordinates уже загружены через selectinload в репозитории, поэтому lazy load не произойдет
    coordinates_list = []
    if hasattr(comment_orm, 'coordinates') and comment_orm.coordinates:
        for coord_orm in comment_orm.coordinates:
            coordinates_list.append(
                CoordinatesSchema(
                    x1=coord_orm.x1,
                    y1=coord_orm.y1,
                    x2=coord_orm.x2,
                    y2=coord_orm.y2
                )
            )
    
    return CommentRead(
        id=comment_orm.id,
        answer_id=comment_orm.answer_id,
        answer_file_key=comment_orm.answer_file_key,
        description=comment_orm.description,
        type_id=comment_orm.type_id,
        coordinates=coordinates_list,
        files=files
    )


async def orm_answer_files_to_ifile_answer(answer_files: list[AnswerFiles]) -> list[IFileAnswer]:
    """
    Преобразование списка AnswerFiles ORM в список IFileAnswer схем.
    
    Args:
        answer_files: Список объектов AnswerFiles из базы данных
        
    Returns:
        Список IFileAnswer с presigned URLs и статусами
    """
    files = []
    if answer_files:
        for answer_file in answer_files:
            try:
                # Получаем presigned URL для файла
                presigned_url = await get_presigned_url(answer_file.key)
                # Создаём IFileAnswer с ключом, URL и статусом AI
                files.append(IFileAnswer(
                    key=answer_file.key,
                    file=presigned_url,
                    ai_status=answer_file.ai_status
                ))
            except Exception as exc:
                logger.warning(f"Failed to get presigned URL for file {answer_file.key}: {exc}")
    return files


async def orm_to_answer_read(answer_orm: Answers) -> AnswerRead:
    """Преобразование Answer ORM в AnswerRead схему"""
    import asyncio

    # Получаем файлы ответов с использованием новой логики
    files = await orm_answer_files_to_ifile_answer(answer_orm.files if answer_orm.files else [])
    
    # Преобразуем assessments и comments
    assessments = [await orm_to_assessment_read(ass) for ass in answer_orm.assessments]
    comments = [await orm_to_comment_read(comm) for comm in answer_orm.comments]
    
    # Преобразуем exercise
    exercise_files = []
    if answer_orm.exercise and answer_orm.exercise.files:
        for key in answer_orm.exercise.files:
            try:
                presigned_url = await get_presigned_url(key)
                exercise_files.append(IFile(key=key, file=presigned_url))
            except Exception as exc:
                logger.warning(f"Failed to get presigned URL for file {key}: {exc}")
    
    exercise_read = None
    if answer_orm.exercise:
        exercise_read = ExerciseRead(
            id=answer_orm.exercise.id,
            task_id=answer_orm.exercise.task_id,
            name=answer_orm.exercise.name,
            description=answer_orm.exercise.description,
            order_index=answer_orm.exercise.order_index,
            files=exercise_files
        )
    
    return AnswerRead(
        id=answer_orm.id,
        work_id=answer_orm.work_id,
        exercise_id=answer_orm.exercise_id,
        text=answer_orm.text,
        general_comment=answer_orm.general_comment,
        files=files,
        exercise=exercise_read,
        assessments=assessments,
        comments=comments
    )


async def orm_to_task_read_for_work(task_orm: Tasks) -> TaskRead:
    """Преобразование Task ORM в TaskRead схему для работы"""
    return TaskRead(
        id=task_orm.id,
        name=task_orm.name,
        description=task_orm.description,
        deadline=str(task_orm.deadline) if task_orm.deadline else None,
        subject_id=task_orm.subject_id  # Добавляем subject_id из модели Tasks
    )


async def orm_to_work_read(work_orm: Works) -> WorkRead:
    """Преобразование Work ORM в WorkRead схему"""
    import asyncio
    
    # Асинхронно преобразуем все ответы
    answers = await asyncio.gather(
        *[orm_to_answer_read(answer) for answer in work_orm.answers]
    )
    
    # Преобразуем задачу
    task_read = await orm_to_task_read_for_work(work_orm.task)
    
    return WorkRead(
        id=work_orm.id,
        task_id=work_orm.task_id,
        student_id=work_orm.student_id,
        finish_date=work_orm.finish_date,
        status=work_orm.status,
        conclusion=work_orm.conclusion or "",
        ai_verificated=work_orm.ai_verificated,
        task=task_read,
        answers=answers
    )


async def apply_work_updates(work_db: Works, update_data: WorkUpdate, user: Users, session: AsyncSession):
    """Применение обновлений к работе с проверкой прав доступа"""
    # Определяем статусы в порядке возрастания
    status_order = {
        StatusWork.draft: 0,
        StatusWork.inProgress: 1,
        StatusWork.verification: 2,
        StatusWork.verificated: 3,
        StatusWork.canceled: 4
    }
    
    if user.role is RoleUser.student:
        # Студент может изменять:
        # - answers.text
        # - answers.files
        # - status (только draft -> inProgress -> verification, нельзя уменьшать)
        
        # Проверка статуса
        if update_data.status != work_db.status:
            # Студент не может обновлять работу со статусом verification или выше
            if work_db.status in [StatusWork.verification, StatusWork.verificated]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Student cannot update work with status beyond 'inProgress'"
                )
            
            # Студент может устанавливать только inProgress или verification
            if update_data.status not in [StatusWork.inProgress, StatusWork.verification]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Student can only set status to 'inProgress' or 'verification'"
                )
            
            # Нельзя уменьшать статус
            if status_order[update_data.status] < status_order[work_db.status]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Status can only be increased or kept the same, not decreased"
                )
            
            work_db.status = update_data.status
        
        # Проверка conclusion - студент не может устанавливать
        if update_data.conclusion and update_data.conclusion != work_db.conclusion:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student cannot set conclusion"
            )
        
        
        # Обновляем answers (только text и files)
        await update_answers_for_student(work_db, update_data.answers, session)
        
    elif user.role is RoleUser.teacher:
        # Учитель может изменять:
        # - answers.general_comment
        # - assessments.points
        # - status (любые, но verificated только после verification)
        # - conclusion


        # Проверка статуса verificated
        if update_data.status == StatusWork.verificated and work_db.status != StatusWork.verification:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Teacher can set 'verificated' only after 'verification'"
            )

        # Проверка finish_date - учитель не может изменять напрямую
        if update_data.finish_date and update_data.finish_date != work_db.finish_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student cannot set finish_date directly"
            )
        
        # Обновляем статус только если он изменился
        if update_data.status != work_db.status:
            work_db.status = update_data.status
        
        # Обновляем conclusion - проверяем явно на None, чтобы можно было установить пустую строку
        if update_data.conclusion is not None:
            work_db.conclusion = update_data.conclusion
        
        # Обновляем finish_date из update_data, если он указан (учитель может изменять)
        if update_data.finish_date is not None:
            work_db.finish_date = update_data.finish_date
        # Или устанавливаем автоматически, если статус изменился на verification или verificated
        elif update_data.status in [StatusWork.verification, StatusWork.verificated] and not work_db.finish_date:
            from datetime import datetime
            work_db.finish_date = datetime.utcnow()
        
        # Обновляем answers (general_comment и assessments)
        await update_answers_for_teacher(work_db, update_data.answers, session)


async def update_answer_files(
    answer_db: Answers,
    files_update: list[IFileAnserUpdate],
    session: AsyncSession
) -> list[str]:
    """
    Обновление файлов ответа: создание, обновление и удаление записей AnswerFiles.
    
    Args:
        answer_db: Объект ответа из базы данных
        files_update: Список файлов для обновления (IFileAnserUpdate)
        session: Сессия базы данных для удаления файлов
        
    Returns:
        Список ключей файлов, которые нужно удалить из S3
    """
    files_to_delete = []
    
    # Создаём словарь существующих файлов по ключу
    existing_files_by_key = {file.key: file for file in (answer_db.files or [])}
    
    # Создаём множество ключей из обновления
    update_keys = {file.key for file in files_update}
    
    # Определяем файлы для удаления (есть в базе, но нет в обновлении)
    keys_to_remove = set(existing_files_by_key.keys()) - update_keys
    
    # Удаляем файлы из базы данных
    for key in keys_to_remove:
        file_to_remove = existing_files_by_key[key]
        files_to_delete.append(key)  # Добавляем ключ для удаления из S3
        session.delete(file_to_remove)  # Удаляем из базы данных
    
    # Обрабатываем файлы из обновления
    for file_update in files_update:
        if file_update.key in existing_files_by_key:
            # Обновляем существующий файл (меняем только ai_status)
            existing_file = existing_files_by_key[file_update.key]
            existing_file.ai_status = file_update.ai_status
        else:
            # Создаём новый файл
            new_file = AnswerFiles(
                answer_id=answer_db.id,
                key=file_update.key,
                ai_status=file_update.ai_status
            )
            answer_db.files.append(new_file)
    
    return files_to_delete


async def update_answers_for_student(work_db: Works, answers_update: list[AnswerUpdate], session: AsyncSession):
    """Обновление ответов студентом (только text и files)"""
    files_to_delete = []
    
    # Создаем словарь существующих ответов по ID
    existing_answers = {answer.id: answer for answer in work_db.answers}

    for answer_update in answers_update:
        answer_id = answer_update.id
        # Обновляем только существующие ответы (студент не может создавать новые)
        if answer_id and answer_id in existing_answers:
            answer_db = existing_answers[answer_id]
            
            # Обновляем только text
            answer_db.text = answer_update.text
            
            # Обрабатываем файлы через новую логику
            if answer_update.files:
                deleted_keys = await update_answer_files(
                    answer_db,
                    answer_update.files,
                    session
                )
                files_to_delete.extend(deleted_keys)
    
    # Удаляем файлы из S3
    if files_to_delete:
        await delete_files_from_s3(files_to_delete)


async def update_answers_for_teacher(work_db: Works, answers_update: list[AnswerUpdate], session: AsyncSession):
    """
    Обновление ответов учителем (general_comment, assessments и ai_status файлов).
    Учитель может обновлять ai_status существующих файлов, но не может добавлять/удалять файлы.
    """
    # Создаем словарь существующих ответов по ID
    existing_answers = {answer.id: answer for answer in work_db.answers}
    
    for answer_update in answers_update:
        answer_id = answer_update.id
        # Обновляем только существующие ответы (учитель не может создавать новые)
        if answer_id and answer_id in existing_answers:
            answer_db = existing_answers[answer_id]
            
            # Обновляем general_comment
            answer_db.general_comment = answer_update.general_comment
            
            # Обновляем ai_status файлов (учитель может только обновлять статусы существующих файлов)
            if answer_update.files:
                # Создаём словарь существующих файлов по ключу
                existing_files_by_key = {file.key: file for file in (answer_db.files or [])}
                
                # Обновляем ai_status только для существующих файлов
                for file_update in answer_update.files:
                    if file_update.key in existing_files_by_key:
                        existing_file = existing_files_by_key[file_update.key]
                        existing_file.ai_status = file_update.ai_status
            
            # Обновляем assessments
            if answer_update.assessments:
                # Создаем словари существующих оценок по id и criterion_id
                existing_assessments_by_id = {
                    ass.id: ass for ass in answer_db.assessments
                }
                existing_assessments_by_criterion = {
                    ass.criterion_id: ass for ass in answer_db.assessments
                }
                
                for assessment_update in answer_update.assessments:
                    # Если есть id, обновляем по id
                    if assessment_update.id and assessment_update.id in existing_assessments_by_id:
                        existing_assessments_by_id[assessment_update.id].points = assessment_update.points
                    # Иначе, если есть criterion_id, обновляем или создаем по criterion_id
                    elif assessment_update.criterion_id:
                        if assessment_update.criterion_id in existing_assessments_by_criterion:
                            # Обновляем существующую оценку
                            existing_assessments_by_criterion[assessment_update.criterion_id].points = assessment_update.points
                        else:
                            # Создаем новую оценку
                            new_assessment = Assessments(
                                answer_id=answer_db.id,
                                criterion_id=assessment_update.criterion_id,
                                points=assessment_update.points
                            )
                            answer_db.assessments.append(new_assessment)