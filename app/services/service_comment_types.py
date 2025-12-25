import uuid

from fastapi import HTTPException
from sqlalchemy.orm import selectinload

from app.exceptions.responses import ErrorNotExists, ErrorRolePermissionDenied, Success
from app.models.model_comments import CommentTypes
from app.models.model_subjects import Subjects
from app.models.model_users import RoleUser, Users
from app.services.schema_base import BaseModelConfig
from app.services.service_base import ServiceBase


from app.utils.logger import logger

class SchemaCommentTypesBase(BaseModelConfig):
    short_name: str
    name: str

class SchemaCommentTypesRead(SchemaCommentTypesBase):
    id: uuid.UUID


class ServiceCommentTypes(ServiceBase):

    async def create(self, id: uuid.UUID, data: SchemaCommentTypesBase, user: Users):
        try:
            if user.role is not RoleUser.admin:
                raise ErrorRolePermissionDenied(RoleUser.admin, user.role)
            
            comment_type = CommentTypes(**data.model_dump())
            comment_type.subject_id = id
            self.session.add(comment_type)
            await self.session.commit()

            return Success(status_code=201)
            
        except HTTPException:
            await self.session.rollback()
            raise
        
        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def get_all(self, subject_id: uuid.UUID, user: Users) -> list[SchemaCommentTypesRead]:
        try:
            subject = await self.session.get(
                Subjects,
                subject_id,
                options=[selectinload(Subjects.comment_types)]
            )

            if not subject:
                raise ErrorNotExists(Subjects)
            print(subject.comment_types)
            return [
                SchemaCommentTypesRead.model_validate(c_type).model_dump(mode="json")
                for c_type in subject.comment_types
            ]

        except HTTPException:
            await self.session.rollback()
            raise
        
        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")

        
    async def update(self, id: uuid.UUID, data: SchemaCommentTypesBase, user: Users):
        try:
            if user.role is not RoleUser.admin:
                raise ErrorRolePermissionDenied(RoleUser.admin, user.role)

            c_type = await self.session.get(CommentTypes, id)
            c_type.short_name = data.short_name
            c_type.name = data.name

            await self.session.commit()

            return Success()

        except HTTPException:
            await self.session.rollback()
            raise
        
        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")
        
    async def delete(self, id: uuid.UUID, user: Users):
        try:
            if user.role is not RoleUser.admin:
                raise ErrorRolePermissionDenied(RoleUser.admin, user.role)

            c_type = await self.session.get(CommentTypes, id)
            await self.session.delete(c_type)

            return Success()
            
        except HTTPException:
            await self.session.rollback()
            raise
        
        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")
        