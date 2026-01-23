import os
import pika
import uuid
from dotenv import load_dotenv

from app.schemas.schema_base import BaseModelConfig

load_dotenv()



class FileRequestDTO(BaseModelConfig):
    id: uuid.UUID
    filename: str

class AnswerRequestDTO(BaseModelConfig):
    id: uuid.UUID
    files: list[FileRequestDTO]

class WorkRequestDTO(BaseModelConfig):
    id: uuid.UUID
    answers: list[AnswerRequestDTO]




credentials = pika.PlainCredentials(
    username=os.getenv("PIKA_USER"),
    password=os.getenv("PIKA_PASSWORD")
)

connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=os.getenv("PIKA_HOST"),
        port=os.getenv("PIKA_PORT"),
        credentials=credentials
    )
)

channel = connection.channel()
