import asyncio
import hashlib
import mimetypes
import time
import uuid
import aioboto3
import os
import boto3
from contextlib import asynccontextmanager
from minio import Minio
from minio.commonconfig import ENABLED, Filter
from minio.lifecycleconfig import LifecycleConfig, Rule, Expiration, AbortIncompleteMultipartUpload
from app.config.config_app import settings
from dotenv import load_dotenv

from app.schemas.schema_files import UploadFileResponse

load_dotenv()

minio_host = os.getenv("MINIO_HOST", "localhost")
minio_port = os.getenv("MINIO_PORT", "9000")
mc = Minio(
    f"{minio_host}:{minio_port}",
    access_key=os.getenv("MINIO_USER"), 
    secret_key=os.getenv("MINIO_PASSWORD"),
    secure=False 
)

# Создаем бакеты, если их нет
if not mc.bucket_exists(settings.BUCKET_PERMANENT):
    mc.make_bucket(settings.BUCKET_PERMANENT)

# --- Асинхронные функции для работы с файлами ---

@asynccontextmanager
async def get_boto_client():
    url = f"http://{minio_host}:{minio_port}"
    session = aioboto3.Session()
    async with session.client(
        's3',
        endpoint_url=url,
        aws_access_key_id=os.getenv("MINIO_USER"),
        aws_secret_access_key=os.getenv("MINIO_PASSWORD"),
        region_name='us-east-1'
    ) as client:
        yield client



async def get_upload_link_to_temp(original_filename: str) -> UploadFileResponse:
    unique_base = f"{uuid.uuid4()}-{time.time()}"
    file_hash = hashlib.sha256(unique_base.encode()).hexdigest()[:15]
    extension, _ = mimetypes.guess_type(original_filename)
    new_filename = f"{file_hash}.{extension.split('/')[1]}" if extension else file_hash

    async with get_boto_client() as s3:
        upload_url = await s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': settings.BUCKET_PERMANENT,
                'Key': new_filename,
                'ContentType': extension
            },
            ExpiresIn=3600
        )

    return UploadFileResponse(
      key=new_filename,
      upload_url=upload_url,
    )

async def get_object_photos(file_keys: list[str]):
    async with get_boto_client() as s3:
        result = {}
        for key in file_keys:
            # Метод generate_presigned_url НЕ требует await
            url = await s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.BUCKET_PERMANENT, 'Key': key},
                ExpiresIn=3600
            )

            result[key] = url
        return result

async def get_presigned_url(filekey: str):
    try:
        async with get_boto_client() as s3:
            url = await s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.BUCKET_PERMANENT, 'Key': filekey},
                ExpiresIn=3600
            )
            return url
    except Exception as e:
      print(f"Ошибка получения ссылки: {e}")
      raise e



async def delete_files_from_s3(file_keys: list[str]):
    if not file_keys: return
    async with get_boto_client() as s3:
        try:
            objects = [{'Key': k} for k in file_keys]
            await s3.delete_objects(
                Bucket=settings.BUCKET_PERMANENT,
                Delete={'Objects': objects, 'Quiet': True}
            )
            await s3.delete_objects(
                Bucket=settings.BUCKET_TEMP,
                Delete={'Objects': objects, 'Quiet': True}
            )
        except Exception as e:
            print(f"Ошибка удаления: {e}")
            raise e