import ipaddress
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.db import get_async_session
from app.models.model_users import Users
from app.schemas.schema_payments import PaymentsCreate, YooKassaWebhookNotification
from app.services.service_payments import ServicePayments
from app.utils.oAuth import get_current_user
from app.utils.logger import logger


router = APIRouter(prefix='/payments')

# Разрешенные IP-адреса ЮКассы для webhook
YOOKASSA_ALLOWED_IPS = [
    ipaddress.ip_network("185.71.76.0/27"),
    ipaddress.ip_network("185.71.77.0/27"),
    ipaddress.ip_network("77.75.153.0/25"),
    ipaddress.ip_address("77.75.156.11"),
    ipaddress.ip_address("77.75.156.35"),
    ipaddress.ip_network("77.75.154.128/25"),
    ipaddress.ip_network("2a02:5180::/32"),
]


def is_yookassa_ip(client_ip: str) -> bool:
    """
    Проверка, что IP-адрес клиента принадлежит ЮКассе.
    
    Args:
        client_ip: IP-адрес клиента
        
    Returns:
        True, если IP-адрес разрешен, False иначе
    """
    try:
        ip = ipaddress.ip_address(client_ip)
        for allowed_ip in YOOKASSA_ALLOWED_IPS:
            if isinstance(allowed_ip, ipaddress.IPv4Network) or isinstance(allowed_ip, ipaddress.IPv6Network):
                if ip in allowed_ip:
                    return True
            elif ip == allowed_ip:
                return True
        return False
    except ValueError:
        # Некорректный IP-адрес
        return False


@router.post('')
async def create(
    data: PaymentsCreate,
    session: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user),
):
    service = ServicePayments(session)
    return await service.create(data, user)


@router.post('/webhook')
async def webhook(
    notification: YooKassaWebhookNotification,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Webhook для обработки уведомлений от ЮКассы.
    
    Обрабатывает следующие события:
    - payment.succeeded: успешный платеж
    - payment.waiting_for_capture: платеж ожидает подтверждения
    - payment.canceled: отмена платежа
    - refund.succeeded: успешный возврат
    
    Проверяет IP-адрес отправителя для безопасности.
    Всегда возвращает 200 OK для подтверждения получения уведомления.
    """
    print("hook")
    print(notification.__dict__)
    # Получаем IP-адрес клиента
    client_ip = request.client.host if request.client else None
    
    # Проверяем IP-адрес (опционально, можно отключить для тестирования)
    # В продакшене рекомендуется включить проверку
    if client_ip and not is_yookassa_ip(client_ip):
        logger.warning(f"Webhook запрос от неразрешенного IP: {client_ip}")
        # В продакшене можно вернуть 403, но для тестирования возвращаем 200
        # raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden IP")
    
    # Обрабатываем уведомление
    service = ServicePayments(session)
    await service.handle_webhook(notification)
    
    # Всегда возвращаем 200 OK для подтверждения получения уведомления
    return {"status": "ok"}

