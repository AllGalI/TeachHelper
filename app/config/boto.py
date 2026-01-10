import asyncio
import hashlib
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
for b in [settings.BUCKET_PERMANENT, settings.BUCKET_TEMP]:
    if not mc.bucket_exists(b):
        mc.make_bucket(b)

# --- Настройка Жизненного Цикла (Lifecycle) ---
def set_minio_lifecycle(bucket_name):
    config = LifecycleConfig(
        [
            Rule(
                status=ENABLED,
                rule_id="DeleteTemporaryFiles",
                # ВАЖНО: prefix="" означает удалять ВСЁ в этом бакете
                rule_filter=Filter(prefix=""), 
                expiration=Expiration(days=1),
                abort_incomplete_multipart_upload=AbortIncompleteMultipartUpload(
                    days_after_initiation=1
                ),
            ),
        ],
    )
    try:
        mc.set_bucket_lifecycle(bucket_name, config)
        print(f"Lifecycle policy установлена для: {bucket_name}")
    except Exception as e:
        print(f"Ошибка Lifecycle: {e}")

set_minio_lifecycle(settings.BUCKET_TEMP)

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

async def get_upload_link_to_temp(original_filename: str):
    unique_base = f"{uuid.uuid4()}-{time.time()}"
    file_hash = hashlib.sha256(unique_base.encode()).hexdigest()[:15]
    extension = original_filename.split('.')[-1] if '.' in original_filename else ''
    new_filename = f"{file_hash}.{extension}" if extension else file_hash
    
    async with get_boto_client() as s3:
        upload_url = await s3.generate_presigned_url(
            'put_object',
            Params={'Bucket': settings.BUCKET_TEMP, 'Key': new_filename},
            ExpiresIn=3600
        )
    return {"file_name": new_filename, "upload_url": upload_url}

async def confirm_file_upload(file_name: str):
    """
    Переносит файл из бакета TEMP в бакет PERMANENT.
    """
    async with get_boto_client() as s3:
        try:
            # Ключ (путь) в обоих бакетах одинаковый — просто имя файла
            copy_source = {
                'Bucket': settings.BUCKET_TEMP,
                'Key': file_name
            }
            
            # Копируем из TEMP в PERMANENT
            await s3.copy_object(
                Bucket=settings.BUCKET_PERMANENT,
                CopySource=copy_source,
                Key=file_name
            )
            
            # Удаляем из TEMP
            await s3.delete_object(Bucket=settings.BUCKET_TEMP, Key=file_name)
            
            print(f"Файл {file_name} подтвержден.")
            return file_name
        except Exception as e:
            print(f"Ошибка подтверждения: {e}")
            raise e

async def get_object_photos(file_keys: list[str]):
    async with get_boto_client() as s3:
        tasks = [
            s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.BUCKET_PERMANENT, 'Key': key},
                ExpiresIn=3600
            ) for key in file_keys
        ]
        return await asyncio.gather(*tasks)

async def delete_files_from_s3(file_keys: list[str]):
    if not file_keys: return
    async with get_boto_client() as s3:
        try:
            objects = [{'Key': k} for k in file_keys]
            return await s3.delete_objects(
                Bucket=settings.BUCKET_PERMANENT,
                Delete={'Objects': objects, 'Quiet': True}
            )
        except Exception as e:
            print(f"Ошибка удаления: {e}")
            raise e