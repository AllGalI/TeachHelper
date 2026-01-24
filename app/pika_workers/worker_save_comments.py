import aio_pika

from app.config.config_app import settings
from app.schemas.schema_AI import SchemaOutgoing
from app.services.service_comments import ServiceComments


async def start_save_worker():
    connection = await aio_pika.connect_robust(settings.pika_url)
    channel = await connection.channel()
    queue = await channel.declare_queue(settings.PIKA_OUTGOING_QUEUE)

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                # Получаем готовый VerificateImageRequest
                data = SchemaOutgoing.model_validate_json(message.body)

                # Логика сохранения в БД
                await ServiceComments.save_ai_results(data)