import aio_pika
from app.config.config_app import settings
from app.exceptions.responses import Success
from app.models.model_users import Users
from app.schemas.schema_AI import AIVerificationRequest
from app.services.service_base import ServiceBase

class ServiceAI(ServiceBase):

    async def ai_verification(self, data: AIVerificationRequest, teacher: Users) -> Success:
      pass

    async def send_to_ai_processing(self, request_data: AIVerificationRequest):
        connection = await aio_pika.connect_robust(settings.pika_url)
        async with connection:
            channel = await connection.channel()
            await channel.default_exchange.publish(
                aio_pika.Message(body=request_data.json().encode()),
                routing_key=settings.PIKA_INCOMING_QUEUE  # Очередь на обработку
            )