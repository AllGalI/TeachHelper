import uuid
import aio_pika
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.config.config_app import settings
from app.exceptions.responses import *
from app.models.model_comments import Comments, Coordinates
from app.models.model_files import AnswerFiles, StatusAnswerFile
from app.models.model_users import RoleUser, Users
from app.models.model_works import Works
from sqlalchemy.orm import selectinload
from app.schemas.schema_AI import SchemaIncomingBack, SchemaOutgoing
from app.schemas.schema_comment import CommentCreate, CommentUpdate
from app.schemas.schema_files import compare_lists
from app.config.boto import delete_files_from_s3
from app.utils.logger import logger
from app.services.service_base import ServiceBase


class ServiceComments(ServiceBase):

    async def send_to_ai_processing(self, data: SchemaIncomingBack, teacher: Users):
        """
        Отправляет полные данные на AI-обработку через RabbitMQ.
        Проверки прав доступа уже выполнены в ServiceAI.ai_verification.
        
        Args:
            data: Полные данные для отправки на AI-обработку (SchemaIncomingBack)
            teacher: Текущий учитель (для логирования/аудита)
            
        Returns:
            Success при успешной отправке
        """
        connection = await aio_pika.connect_robust(settings.pika_url)
        async with connection:
            channel = await connection.channel()

            await channel.default_exchange.publish(
                aio_pika.Message(body=data.model_dump_json().encode()),
                routing_key=settings.PIKA_INCOMING_QUEUE
            )
        await self.session.commit()
        return Success()

    async def save_ai_results(
        self,
        data: SchemaOutgoing
    ):
        try:
            for answer in data.answers:
                orm_comments: list[Comments] = []
                for comment in answer.comments:
                    comment_orm = Comments(
                        answer_id=comment.answer_id,
                        answerfile_id=comment.answerfile_id,
                        description=comment.description,
                        type_id=comment.type_id,
                        human=False,
                    )

                    for coordinate in comment.coordinates:
                        comment_orm.coordinates.append(Coordinates(
                            x1=coordinate.x1,
                            y1=coordinate.y1,
                            x2=coordinate.x2,
                            y2=coordinate.y2,
                        ))
                    orm_comments.append(comment_orm)
                self.session.add_all(orm_comments)

                # Обрабатываем файлы: обновляем существующие или создаём новые
                for a_file in answer.files:
                    # Проверяем, существует ли файл с таким id в БД
                    existing_file = await self.session.get(AnswerFiles, a_file.id)
                    
                    if existing_file:
                        # Файл существует - обновляем его статус
                        existing_file.ai_status = a_file.ai_status
                        # Обновляем ключ, если он изменился
                        if existing_file.key != a_file.key:
                            existing_file.key = a_file.key
                    else:
                        # Файл не существует - создаём новый
                        new_file = AnswerFiles(
                            id=a_file.id,
                            answer_id=answer.id,
                            key=a_file.key,
                            ai_status=a_file.ai_status,
                        )
                        self.session.add(new_file)
                

                await self.session.commit()

            return Success()

        except HTTPException:
            raise
        
        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")


    async def create(
        self,
        comment: CommentCreate,
        user: Users,
    ):
        try:
            if user.role is RoleUser.student:
                raise ErrorRolePermissionDenied(RoleUser.teacher, user.role)

            comment_orm = Comments(
                answer_id=comment.answer_id,
                answerfile_id=comment.answerfile_id,
                description=comment.description,
                type_id=comment.type_id,
                human=comment.human,
                files=comment.files
            )

            comment_orm.coordinates.extend(
              Coordinates(
                x1=coordinate.x1,
                y1=coordinate.y1,
                x2=coordinate.x2,
                y2=coordinate.y2,
              ) for coordinate in comment.coordinates)

            self.session.add(comment_orm)
            await self.session.commit()
            return Success()

        except HTTPException:
            raise
        
        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def update(self, comment_id: uuid.UUID, update_data: CommentUpdate, user: Users):
        """
        Обновление комментария с обработкой файлов.
        
        При обновлении файлов:
        1. Сравнивается старый и новый список файлов
        2. Удаленные файлы автоматически удаляются из S3
        3. Обновляется список файлов в базе данных
        """
        try:
            if user.role is RoleUser.student:
                raise ErrorRolePermissionDenied(RoleUser.teacher, RoleUser.student)

            comment_db = await self.session.get(Comments, comment_id)
            if comment_db is None:
                raise ErrorNotExists(Comments)

            # Обрабатываем файлы отдельно, если они переданы
            files_to_delete = []
            if update_data.files is not None:
                # Сравниваем старый и новый список файлов
                old_files = comment_db.files if comment_db.files else []
                file_changes = compare_lists(old_files, update_data.files)
                files_to_delete = file_changes['removed']
                # Обновляем список файлов
                comment_db.files = update_data.files

            # Обновляем остальные поля (type_id, description)
            update_payload = update_data.model_dump(exclude_unset=True, exclude={'files'})  # исключаем files, т.к. уже обработали
            for key, value in update_payload.items():
                if hasattr(comment_db, key):
                    setattr(comment_db, key, value)

            # Удаляем файлы из S3, если есть удаленные
            if files_to_delete:
                try:
                    await delete_files_from_s3(files_to_delete)
                except Exception as s3_exc:
                    # Логируем ошибку, но продолжаем обновление комментария
                    logger.warning(f"Failed to delete files from S3: {s3_exc}")

            await self.session.commit()
            return JSONResponse(
                content={"status": "ok"},
                status_code=200
            )

        except HTTPException:
            await self.session.rollback()
            raise
        
        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")


    async def delete(self, comment_id: uuid.UUID, user: Users):
        try:
            if user.role is RoleUser.student:
                raise ErrorRolePermissionDenied(RoleUser.teacher, RoleUser.student)

            comment_db = await self.session.get(
                Comments,
                comment_id,
            )

            if comment_db is None:
                raise ErrorNotExists(Comments)


            await self.session.delete(comment_db)
            await self.session.commit()
            return JSONResponse({"status": "ok"}, 200)


        except HTTPException:
            await self.session.rollback()
            raise
        
        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")


