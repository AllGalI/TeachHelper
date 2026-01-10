
import enum
import uuid

from fastapi import HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.boto import delete_files_from_s3, get_boto_client, get_upload_link_to_temp
from app.config.config_app import settings
from app.exceptions.responses import *
from app.models.model_users import RoleUser, Users
from app.schemas.schema_files import FileSchema
from app.utils.file_validation import validate_files
from app.utils.logger import logger
from app.services.service_base import ServiceBase



class ServiceFiles(ServiceBase):

    async def create(self, filename: str):
        try:
            response = await get_upload_link_to_temp(filename)
            return response
        except HTTPException:
            await self.session.rollback()
            raise
        
        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")


    async def delete(self, keys: list[str]):
        try:
            await delete_files_from_s3(keys)
            return JSONResponse(
                {"status": "ok"},
                200
            )

        except Exception as exc:
            logger.exception(exc)
            raise HTTPException(status_code=500, detail="Internal Server Error")

