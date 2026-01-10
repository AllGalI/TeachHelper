import asyncio
from logging import Filter
import hashlib
import time
import uuid
import aioboto3
import os
from contextlib import asynccontextmanager
from minio import Minio
from minio.commonconfig import ENABLED
from minio.lifecycleconfig import AbortIncompleteMultipartUpload, Expiration, LifecycleConfig
from minio.sseconfig import Rule
from app.config.config_app import settings
from dotenv import load_dotenv
load_dotenv()

# Инициализация MinIO клиента с использованием переменных окружения
minio_host = os.getenv("MINIO_HOST", "localhost")
minio_port = os.getenv("MINIO_PORT", "9000")
mc = Minio(
    f"{minio_host}:{minio_port}",
    access_key=os.getenv("MINIO_USER"), 
    secret_key=os.getenv("MINIO_PASSWORD"),
    secure=False  # Для HTTP (не HTTPS)
)

if not mc.bucket_exists(settings.BUCKET_PERMANENT):
  mc.make_bucket(settings.BUCKET_PERMANENT)

if not mc.bucket_exists(settings.BUCKET_TEMP):
  mc.make_bucket(settings.BUCKET_TEMP)


def set_minio_lifecycle(bucket_name):
    # Создаем конфигурацию жизненного цикла
    config = LifecycleConfig(
        [
            Rule(
                status=ENABLED,
                rule_id="DeleteTemporaryFiles",
                rule_filter=Filter(prefix=f"{bucket_name}/"),
                # Удаление объекта через 1 день
                expiration=Expiration(days=1),
                # Очистка незавершенных загрузок (частей файлов) через 1 день
                abort_incomplete_multipart_upload=AbortIncompleteMultipartUpload(
                    days_after_initiation=1
                ),
            ),
        ],
    )

    try:
        # В minio-py метод называется set_bucket_lifecycle
        mc.set_bucket_lifecycle(bucket_name, config)
        print(f"Lifecycle policy успешно установлена для бакета: {bucket_name}")
    except Exception as e:
        print(f"Ошибка при установке lifecycle policy: {e}")

# Использование
set_minio_lifecycle(settings.BUCKET_TEMP)

def set_cors_configuration(bucket_name):
    # Определяем правила CORS
    # Мы разрешаем PUT (для загрузки) и GET (для чтения)
    cors_configuration = {
        'CORSRules': [
            {
                'AllowedHeaders': ['*'], # Разрешаем любые заголовки (Content-Type и т.д.)
                'AllowedMethods': ['PUT', 'GET', 'POST', 'HEAD'], 
                'AllowedOrigins': ['*'], # В продакшене лучше заменить на ваш домен, например ['https://my-app.com']
                'ExposeHeaders': ['ETag'],
                'MaxAgeSeconds': 3000
            }
        ]
    }

    try:
        # Для MinIO через boto3 (так как у minio-py специфичный интерфейс для этого)
        import boto3
        s3 = boto3.client(
            's3',
            endpoint_url=f"http://{os.getenv('MINIO_HOST')}:{os.getenv('MINIO_PORT')}",
            aws_access_key_id=os.getenv("MINIO_USER"),
            aws_secret_access_key=os.getenv("MINIO_PASSWORD")
        )
        
        s3.put_bucket_cors(
            Bucket=bucket_name,
            CORSConfiguration=cors_configuration
        )
        print(f"CORS успешно настроен для бакета: {bucket_name}")
    except Exception as e:
        print(f"Ошибка при настройке CORS: {e}")

# Применяем для обоих бакетов
set_cors_configuration(settings.BUCKET_TEMP)
set_cors_configuration(settings.BUCKET_PERMANENT)


@asynccontextmanager
async def get_boto_client():
    url = f"http://{os.getenv("MINIO_HOST")}:{os.getenv("MINIO_PORT")}"
    session = aioboto3.Session()
    async with session.client(
        's3',
        endpoint_url=url,  # Для MinIO
        aws_access_key_id=os.getenv("MINIO_USER"),
        aws_secret_access_key=os.getenv("MINIO_PASSWORD"),
        region_name='us-east-1'
    ) as client:
        yield client


async def get_upload_link_to_temp(original_filename: str):
    """
    Генерирует уникальное имя файла и временную ссылку для загрузки в бакет TEMP.
    """
    # 1. Генерируем уникальный хеш длиной 15 символов
    # Берем UUID + время для полной уникальности
    unique_base = f"{uuid.uuid4()}-{time.time()}"
    file_hash = hashlib.sha256(unique_base.encode()).hexdigest()[:15]
    
    # 2. Сохраняем расширение исходного файла
    extension = original_filename.split('.')[-1] if '.' in original_filename else ''
    new_filename = f"{file_hash}.{extension}" if extension else file_hash
    
    async with get_boto_client() as s3:
        # 3. Генерируем Pre-signed URL для метода PUT
        # Фронтенд использует эту ссылку, чтобы отправить файл напрямую
        upload_url = await s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': settings.BUCKET_TEMP,
                'Key': new_filename,
                # Можно раскомментировать, если нужно ограничить тип файла:
                # 'ContentType': 'image/jpeg' 
            },
            ExpiresIn=3600  # Ссылка действительна 1 час
        )

    return {
        "file_name": new_filename,  # Это имя нужно сохранить на фронте и прислать при создании объекта
        "upload_url": upload_url    # По этой ссылке фронт делает PUT запрос с файлом
    }


async def confirm_file_upload(file_name: str):
    """
    Переносит файл из папки temp/ в папку permanent/ внутри одного бакета.
    """
    temp_key = f"{settings.BUCKET_TEMP}/{file_name}"
    permanent_key = f"{settings.BUCKET_PERMANENT}/{file_name}"

    async with get_boto_client() as s3:
        try:
            # 1. Копируем объект
            # Обрати внимание: в CopySource нужно указывать путь вместе с именем бакета
            copy_source = {
                'Bucket': settings.BUCKET_TEMP,
                'Key': temp_key
            }
            
            await s3.copy_object(
                Bucket=settings.BUCKET_PERMANENT,
                CopySource=copy_source,
                Key=permanent_key
            )
            
            # 2. Удаляем временный файл
            await s3.delete_object(Bucket=settings.BUCKET_TEMP, Key=temp_key)
            
            print(f"Файл {file_name} успешно перенесен в permanent/")
            return permanent_key

        except Exception as e:
            print(f"Ошибка при подтверждении файла: {e}")
            raise e


async def get_object_photos(file_keys: list[str]):
    """
    Принимает список ключей из БД ['key1.jpg', 'key2.jpg']
    Возвращает список временных ссылок.
    """
    async with get_boto_client() as s3:
        tasks = []
        for key in file_keys:
            # Создаем задачу на генерацию ссылки для каждого ключа
            tasks.append(
                s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': settings.BUCKET_PERMANENT, 'Key': key},
                    ExpiresIn=3600  # Ссылка будет работать 1 час
                )
            )
        
        # Выполняем все генерации параллельно
        urls = await asyncio.gather(*tasks)
        return urls


async def delete_files_from_s3(file_keys: list[str]):
    """
    Удаляет список файлов из бакета BUCKET_PERMANENT.
    Принимает список ключей, например: ['hash1.jpg', 'hash2.png']
    """
    if not file_keys:
        return

    async with get_boto_client() as s3:
        try:
            # Формируем структуру для удаления
            objects_to_delete = [{'Key': key} for key in file_keys]
            
            response = await s3.delete_objects(
                Bucket=settings.BUCKET_PERMANENT,
                Delete={
                    'Objects': objects_to_delete,
                    'Quiet': True  # Если True, S3 не будет возвращать список удаленных объектов в ответе
                }
            )
            
            return response

        except Exception as e:
            print(f"Ошибка при удалении файлов из S3: {e}")
            # В зависимости от логики, тут можно либо пробросить ошибку, 
            # либо просто залогировать её, чтобы удаление в БД не прерывалось
            raise e