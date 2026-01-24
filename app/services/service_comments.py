import uuid
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.exceptions.responses import *
from app.models.model_comments import Comments, Coordinates
from app.models.model_files import StatusAnswerFile
from app.models.model_users import RoleUser, Users
from app.models.model_works import Answers, Works
from app.schemas.schema_AI import AnswerFiles, SchemaOutgoing
from app.schemas.schema_comment import CommentCreate, CommentUpdate
from app.schemas.schema_files import compare_lists
from app.config.boto import delete_files_from_s3
from app.utils.logger import logger
from app.services.service_base import ServiceBase


class ServiceComments(ServiceBase):
    @staticmethod
    async def save_ai_results(
        self,
        data: SchemaOutgoing
    ):
        try:
            for answer in data.answers:
                for comments in answer.comments:
                    orm_comments: list[Comments] = []
                    for comment in comments:
                        comment_orm = Comments(
                            answer_id=comment.answer_id,
                            answer_file_key=comment.answer_file_key,
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
                    answer_file = await self.session.get(AnswerFiles, comment.answerfile_id)
                    answer_file.ai_status = StatusAnswerFile.verified

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
                answer_file_key=comment.answer_file_key,
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


