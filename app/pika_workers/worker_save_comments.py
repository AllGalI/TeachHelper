import aio_pika

from app.config.config_app import settings
from app.config.db import AsyncSessionLocal
from app.schemas.schema_AI import SchemaOutgoing
from app.services.service_comments import ServiceComments
from app.utils.logger import logger


async def start_save_worker():
    """
    Worker для сохранения результатов AI-обработки в БД.
    Создаёт новую сессию БД для каждого сообщения из очереди.
    """
    connection = await aio_pika.connect_robust(settings.pika_url)
    channel = await connection.channel()
    queue = await channel.declare_queue(settings.PIKA_OUTGOING_QUEUE)

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                # Создаём новую сессию БД для каждого сообщения
                async with AsyncSessionLocal() as session:
                    try:
                        # Получаем данные из сообщения
                        data = SchemaOutgoing.model_validate_json(message.body)
                        logger.info(f"Processing AI results for {len(data.answers)} answers")
                        
                        # Создаём сервис с сессией и сохраняем результаты
                        service = ServiceComments(session)
                        await service.save_ai_results(data)
                        
                        logger.info("Successfully saved AI results to database")
                    except Exception as exc:
                        # Логируем ошибку, но не прерываем обработку других сообщений
                        logger.exception(f"Error processing AI results: {exc}")
                        # Сессия автоматически откатится при выходе из контекста
                        raise  # Повторно выбрасываем исключение, чтобы сообщение вернулось в очередь