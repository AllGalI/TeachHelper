import asyncio
import os
from fastapi import Depends
import pika
import uuid
from dotenv import load_dotenv
from sqlalchemy import select

from app.db import get_async_session
from app.models.model_comments import CommentTypes, Comments
from app.models.model_subjects import Subjects
from app.models.model_tasks import Tasks
from app.models.model_works import Answers, Works
from app.schemas.pika.schema_htr import AICommentDTO, Coordinates
from app.services.schema_base import BaseModelConfig
from app.services.service_comments import ServiceComments
from app.utils.logger import logger

load_dotenv()


class Coordinates(BaseModelConfig):
    x1: float
    y1: float
    x2: float
    y2: float

class AICommentDTO(BaseModelConfig):
    image_file_id: uuid.UUID
    description: str
    type: str
    coordinates: list[Coordinates]

class AnswerResponseDTO(BaseModelConfig):
    id: uuid.UUID
    comments: list[AICommentDTO]

class WorkResponseDTO(BaseModelConfig):
    id: uuid.UUID
    answers: list[AnswerResponseDTO]


class FileRequestDTO(BaseModelConfig):
    id: uuid.UUID
    filename: str

class AnswerRequestDTO(BaseModelConfig):
    id: uuid.UUID
    files: list[FileRequestDTO]

class WorkRequestDTO(BaseModelConfig):
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

    def on_response(self, ch, method, props, body):
        if self.corr_id != props.correlation_id:
            raise Exception(f"queue response for wrong work_id")

        self.response = WorkResponseDTO.model_validate(body)

    def call(self, body: WorkRequestDTO):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange="",
            routing_key="htr_queue",
            properties=pika.BasicProperties(
                content_type="application/json",
                reply_to=self.callback_queue,
                correlation_id=self.corr_id
            ),
            body=body.model_dump_json().encode()
        )
        
        while self.response is None:
            self.connection.process_data_events(time_limit=None)

        asyncio.run(save_comments(self.response))


async def save_comments(response: WorkResponseDTO):
    async with get_async_session() as session:
        try:
            types_stmt = (
                select(CommentTypes.id, CommentTypes.name)
                .join(Subjects, CommentTypes.subject_id == Subjects.id)
                .join(Tasks, Subjects.id == Tasks.subject_id)
                .join(Works, Tasks.id == Works.task_id)
                .where(Works.id == response.id)
            )

            response = await session.execute(types_stmt)
            types_orm = response.scalars().all()
            types = {type_orm.name:type_orm.id for type_orm in types_orm}
            
            comments: list[Comments] = []
            for answer in response.answers:
                for comment in answer.comments:
                    comments.append(
                        Comments(
                            image_file_id=answer.image_file_id,
                            description=comment.description,
                            type_id=types[comment.type],
                            coordinates=comment.coordinates,
                        )
                    )
            session.add_all(comments)
            await session.commit()

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