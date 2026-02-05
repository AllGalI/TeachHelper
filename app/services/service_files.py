
import enum
import uuid

from fastapi import HTTPException
from fastapi.responses import JSONResponse

from app.config.boto import delete_files_from_s3, get_presigned_url, get_upload_link_to_temp
from app.config.config_app import settings
from app.exceptions.responses import *
from app.models.model_users import Users
from app.schemas.schema_files import UploadFileResponse, UploadFileResponse
from app.utils.logger import logger
from app.services.service_base import ServiceBase



class ServiceFiles(ServiceBase):

    async def create(self, file_name: str, user: Users)-> UploadFileResponse:
        try:
            s3_response: UploadFileResponse = await get_upload_link_to_temp(file_name)
            return {
              "upload_link": s3_response.upload_link,
              "key": s3_response.key
            }

        except HTTPException as exc:
            await self.session.rollback()
            print(exc)
            raise
        
        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")


    async def delete(self, keys: list[str]) -> JSONResponse:
        try:
            await delete_files_from_s3(keys)
            return JSONResponse(
                {"status": "ok"},
                200
            )

        except Exception as exc:
            logger.exception(exc)
            raise HTTPException(status_code=500, detail="Internal Server Error")

