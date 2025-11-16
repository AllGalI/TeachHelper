import asyncio
import os
from fastapi import Depends
import pika
import uuid
from dotenv import load_dotenv
from pydantic import BaseModel

from app.db import get_async_session
from app.models.model_works import Answers, Works
from app.services.service_comments import ServiceComments
from app.utils.logger import logger

load_dotenv()

class CommentResponseDTO(BaseModel):
    description: str
    type_name: str
    x1: float
    y1: float
    x2: float
    y2: float

class AnswerResponseDTO(BaseModel):
    id: uuid.UUID
    comments: list[CommentResponseDTO]

class WorkResponseDTO(BaseModel):
    id: uuid.UUID
    answers: list[AnswerResponseDTO]


class FileRequestDTO(BaseModel):
    id: uuid.UUID
    filename: str

class AnswerRequestDTO(BaseModel):
    id: uuid.UUID
    files: list[FileRequestDTO]

class WorkRequestDTO(BaseModel):
    id: uuid.UUID
    answers: list[AnswerRequestDTO]


class ClientHTRRpc(object):
    def __init__(self):
        
        self.credentials = pika.PlainCredentials(
            username=os.getenv("PIKA_USER"),
            password=os.getenv("PIKA_PASSWORD")
        )
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=os.getenv("PIKA_HOST"),
                port=os.getenv("PIKA_PORT"),
                credentials=self.credentials
            )
        )
        
        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True
        )

        self.response = None
        self.corr_id = None

    async def on_response(self, ch, method, props, body):
        body = WorkResponseDTO.model_validate(body)
        if self.corr_id != props.correlation_id:
            raise Exception(f"queue response for wrong work_id")
        return body

    async def call(self, body: WorkRequestDTO):
        self.response = None
        self.corr_id == str(uuid.uuid4())
        self.channel.basic_publish(
            exchange="",
            routing_key="htr_queue",
            properties=pika.BasicProperties(
                content_type="WorkRequestDTO",
                reply_to=self.callback_queue,
                correlation_id=self.corr_id
            ),
            body=body
        )
        
        while self.response is None:
            self.connection.process_data_events(time_limit=None)

        return self.response


async def save_comments(response: WorkResponseDTO):
    async with get_async_session() as session:
        try:        
            work_db = await session.get(Works, response.id)
            if work_db is None:
                raise Exception("Work from queue not exitst")

            for answer_queue in response.answers:
                answer_db = await session.get(
                    Answers,
                    answer_queue.id,
                    options={"Answers.comments"}
                )

                if answer_db is None:
                    raise Exception("Work from queue not exitst")

                answer_db.comments += answer_queue.comments
                await session.flush()

        except Exception as exc:
            logger.exception(exc)


if __name__ == "__main__":
    htr = ClientHTRRpc()

    resposne = asyncio.run(htr.call(WorkRequestDTO(
        uuid.uuid4(),
        answers=[
            AnswerRequestDTO(
                uuid.uuid4(),
                files = [
                    FileRequestDTO(
                        uuid.uuid4,
                        "filename.jpg"
                    )
                ]
            )
        ]
    )))