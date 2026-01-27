from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config.config_app import settings
from app.exceptions.responses import ErrorNotExists, ErrorPermissionDenied, ErrorRolePermissionDenied, Success
from app.models.model_comments import CommentTypes
from app.models.model_files import AnswerFiles, StatusAnswerFile
from app.models.model_subjects import Subjects
from app.models.model_tasks import Tasks
from app.models.model_users import RoleUser, Users
from app.models.model_works import Works
from app.schemas.schema_AI import SchemaIncomingBack, SchemaIncomingFront
from app.schemas.schema_comment import SchemaCommentTypesRead
from app.services.service_base import ServiceBase
from app.services.service_comments import ServiceComments
from app.utils.logger import logger


class ServiceAI(ServiceBase):

    async def ai_verification(self, data: SchemaIncomingFront, teacher: Users) -> Success:
        """
        Принимает ограниченные данные с фронтенда, собирает недостающие данные из БД
        и отправляет полные данные на AI-обработку.
        
        Args:
            data: Ограниченные данные с фронтенда (work_id и answers)
            teacher: Текущий учитель
            
        Returns:
            Success при успешной отправке
        """
        try:
            if teacher.role is not RoleUser.teacher:
                raise ErrorRolePermissionDenied(RoleUser.teacher, teacher.role)
            
            # Получаем работу с загруженной задачей и предметом для проверки принадлежности
            stmt = (
                select(Works)
                .where(Works.id == data.work_id)
                .options(
                    selectinload(Works.task).selectinload(Tasks.subject).selectinload(Subjects.comment_types)
                )
            )
            result = await self.session.execute(stmt)
            work_db = result.scalars().first()
            
            # Проверяем, что работа существует
            if work_db is None:
                raise ErrorNotExists(Works)
            
            # Проверяем, что задача принадлежит текущему учителю
            if work_db.task.teacher_id != teacher.id:
                raise ErrorPermissionDenied()
            
            # Получаем типы комментариев для предмета задачи
            comment_types = [
                SchemaCommentTypesRead(
                    id=ct.id,
                    short_name=ct.short_name,
                    name=ct.name
                )
                for ct in work_db.task.subject.comment_types
            ]
            
            # Обновляем статусы файлов ответов на "pending" (на проверке) перед отправкой
            file_ids_to_update = []
            for answer in data.answers:
                for file in answer.files:
                    file_ids_to_update.append(file.id)
            
            # Обновляем статусы файлов в БД
            if file_ids_to_update:
                stmt_files = select(AnswerFiles).where(AnswerFiles.id.in_(file_ids_to_update))
                result_files = await self.session.execute(stmt_files)
                files_to_update = result_files.scalars().all()
                
                for file_db in files_to_update:
                    file_db.ai_status = StatusAnswerFile.pending
                
                # Сохраняем изменения в БД
                await self.session.flush()
            
            # Формируем полную схему для отправки на AI-обработку
            schema_back = SchemaIncomingBack(
                work_id=data.work_id,
                task_id=work_db.task_id,
                status=work_db.status,
                comment_types=comment_types,
                answers=data.answers
            )

            # Отправляем на обработку через ServiceComments
            service_comments = ServiceComments(self.session)
            return await service_comments.send_to_ai_processing(schema_back, teacher)
            
        except HTTPException:
            await self.session.rollback()
            raise
        
        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")