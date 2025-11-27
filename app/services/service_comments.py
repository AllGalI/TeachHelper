import uuid
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.exceptions.responses import *
from app.models.model_comments import Comments, Coordinates
from app.models.model_users import RoleUser, Users
from app.models.model_works import Answers, Works
from app.schemas.schema_comment import AICommentDTO, CommentUpdate
from app.utils.logger import logger
from app.services.service_base import ServiceBase


class ServiceComments(ServiceBase):

    async def ai_create(
        self,
        work_id: uuid.UUID,
        comments: list[AICommentDTO],
        user: Users,
    ):
        try:
            if user.role is not RoleUser.admin:
                logger.exception(f"User: {user.id}, tried to create ai_comment")
                raise ErrorPermissionDenied()
            """
            Добавить пользователся HtrClient и дать ему возможность создавать комментарии
            """
            orm_comments: list[Comments] = []
            for comment in comments:
                comment_orm = Comments(
                    answer_id=comment.answer_id,
                    answer_file_id=comment.image_file_id,
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
            work_db = await self.session.get(Works, work_id)
            work_db.ai_verificated = True

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
        answer_id: uuid.UUID,
        comments: list[AICommentDTO],
        user: Users,
    ):
        try:
            if user.role is RoleUser.student:
                raise ErrorRolePermissionDenied(RoleUser.teacher, user.role)
            """
            Добавить пользователся HtrClient и дать ему возможность создавать комментарии
            """
            orm_comments: list[Comments] = []

            for comment in comments:
                comment_orm = Comments(
                    answer_id=answer_id,
                    answer_file_id=comment.image_file_id,
                    description=comment.description,
                    type_id=comment.type_id,
                    human=True,
                )
                comment_orm.coordinates.extend(comment.coordinates)

            self.session.add_all(orm_comments)
            await self.session.commit()
            return Success()

        except HTTPException:
            raise
        
        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def update(self, comment_id: uuid.UUID, update_data: CommentUpdate, user: Users):
        try:
            if user.role is RoleUser.student:
                raise ErrorRolePermissionDenied(RoleUser.teacher, RoleUser.student)

            comment_db = await self.session.get(Comments, comment_id)
            if comment_db is None:
                raise ErrorNotExists(Comments)

            update_payload = update_data.model_dump(exclude_unset=True)  # обновляем только переданные поля, остальное не трогаем
            for key, value in update_payload.items():
                if hasattr(comment_db, key):
                    setattr(comment_db, key, value)

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


