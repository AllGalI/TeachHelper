import os
import pika
import uuid
from dotenv import load_dotenv

import aio_pika
from app.config.config_app import settings
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


# def get_rabbit_channel():
#     credentials = pika.PlainCredentials(
#         username=os.getenv("PIKA_USER"),
#         password=os.getenv("PIKA_PASSWORD")
#     )

#     connection = pika.BlockingConnection(
#         pika.ConnectionParameters(
#             host=os.getenv("PIKA_HOST"),
#             port=int(os.getenv("PIKA_PORT")),
#             credentials=credentials,
#             heartbeat=600,
#         )
#     )

#     return connection.channel()


connection: aio_pika.RobustConnection | None = None
channel: aio_pika.abc.AbstractChannel | None = None


async def init_rabbit():
    global connection, channel
    connection = await aio_pika.connect_robust(settings.pika_url)
    channel = await connection.channel()


async def close_rabbit():
    if connection:
        await connection.close()


def get_rabbit_channel():
    if channel is None:
        raise RuntimeError("RabbitMQ channel is not initialized")
    return channel