import uuid
from datetime import datetime
from typing import Optional
from app.config.config_app import settings
from app.schemas.schema_base import BaseModelConfig


class PaymentsCreate(BaseModelConfig):
    plan_id: uuid.UUID


# Схемы для webhook уведомлений от ЮКассы
class YooKassaAmount(BaseModelConfig):
    """Схема для суммы платежа в уведомлении"""
    value: str
    currency: str


class YooKassaPaymentMethod(BaseModelConfig):
    """Схема для способа оплаты в уведомлении"""
    type: str
    id: Optional[str] = None
    saved: Optional[bool] = None


class YooKassaPaymentObject(BaseModelConfig):
    """Схема для объекта платежа в уведомлении"""
    id: str
    status: str
    paid: bool
    amount: YooKassaAmount
    created_at: datetime
    description: Optional[str] = None
    payment_method: Optional[YooKassaPaymentMethod] = None
    metadata: Optional[dict] = None


class YooKassaRefundObject(BaseModelConfig):
    """Схема для объекта возврата в уведомлении"""
    id: str
    status: str
    amount: YooKassaAmount
    created_at: datetime
    payment_id: str
    metadata: Optional[dict] = None


class YooKassaWebhookNotification(BaseModelConfig):
    """Схема для webhook уведомления от ЮКассы"""
    type: str  # "notification"
    event: str  # "payment.succeeded", "payment.waiting_for_capture", "payment.canceled", "refund.succeeded"
    object: YooKassaPaymentObject | YooKassaRefundObject  # Объект платежа или возврата
