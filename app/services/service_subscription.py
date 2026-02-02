from datetime import datetime, timedelta, timezone
import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.responses import ErrorNotExists
from app.models.model_subscription import Subscriptions, Payments, Plans
from app.repositories.repo_subscription import RepoSubscription
from app.schemas.schema_subscription import SubscriptionCancel, SubscriptionStartPeriodRequest, SubscriptionRead
from app.services.service_base import ServiceBase
from app.utils.logger import logger


class ServiceSubscription(ServiceBase):
    """Сервис для управления подписками"""

    async def cancel_subscription(self, data: SubscriptionCancel, user_id: uuid.UUID) -> dict:
        """
        Отмена подписки с проверкой условий возврата средств.
        
        Условия возврата:
        - В течение 14 дней с момента оплаты
        - Использование не превышает лимит для тарифа
        - Если условия выполнены - возврат возможен
        
        Args:
            data: Данные для отмены подписки (id подписки)
            user_id: ID пользователя, отменяющего подписку
            
        Returns:
            Словарь с информацией о результате отмены
        """
        try:
            repo = RepoSubscription(self.session)
            subscription = await repo.get(data.id)
            
            if subscription is None:
                raise ErrorNotExists(Subscriptions)
            
            # Проверяем, что подписка принадлежит пользователю
            if subscription.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="У вас нет прав на отмену этой подписки"
                )
            
            # Получаем план для проверки лимитов
            if subscription.plan is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="План подписки не найден"
                )
            
            # Получаем лимит возврата из плана
            refund_limit = subscription.plan.refund_limits
            
            # Находим платеж для этой подписки
            stmt = (
                select(Payments)
                .where(
                    Payments.subscription_id == subscription.id,
                    Payments.status == PaymentStatus.paid
                )
                .order_by(Payments.paid_at.desc())
            )
            result = await self.session.execute(stmt)
            payment = result.scalar_one_or_none()
            
            if payment is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Платеж для этой подписки не найден"
                )
            
            # Проверяем условия возврата
            # payment.paid_at уже имеет timezone, поэтому используем now() с timezone
            now_utc = datetime.now(timezone.utc)
            # Если paid_at имеет timezone, используем его, иначе считаем UTC
            paid_at_utc = payment.paid_at if payment.paid_at.tzinfo else payment.paid_at.replace(tzinfo=timezone.utc)
            days_since_payment = (now_utc - paid_at_utc).days
            can_refund = False
            refund_reason = ""
            
            # Проверка 1: В течение 14 дней с момента оплаты
            if days_since_payment > 14:
                refund_reason = "Возврат возможен только в течение 14 дней с момента оплаты"
            # Проверка 2: Использование не превышает лимит
            elif subscription.used_checks > refund_limit:
                refund_reason = (
                    f"Возврат невозможен: использовано {subscription.used_checks} проверок, "
                    f"лимит для возврата: {refund_limit}"
                )
            else:
                can_refund = True
                refund_reason = "Условия для возврата выполнены"
            
            # Если возврат возможен, обновляем статус платежа
            if can_refund:
                payment.status = PaymentStatus.refunded
                # Здесь должна быть логика возврата через платежную систему (ЮКасса)
                # Пока просто обновляем статус в БД
                await self.session.commit()
                
                return {
                    "status": "success",
                    "message": "Подписка отменена, возврат средств будет обработан",
                    "refund_amount": payment.amount,
                    "refund_currency": payment.currency
                }
            else:
                # Отменяем подписку без возврата: устанавливаем finish_at на текущую дату
                subscription.finish_at = datetime.now(timezone.utc)
                await self.session.commit()
                
                return {
                    "status": "cancelled",
                    "message": "Подписка отменена, но возврат средств невозможен",
                    "reason": refund_reason
                }
                
        except HTTPException:
            await self.session.rollback()
            raise
        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def start_new_period(
        self, data: SubscriptionStartPeriodRequest, user_id: uuid.UUID
    ) -> SubscriptionRead:
        """
        Начало нового периода подписки: обновление plan_id, сброс used_checks
        и self_writing, установка новых started_at и finish_at по плану.
        """
        repo = RepoSubscription(self.session)
        subscription = await repo.get(data.id)
        if subscription is None:
            raise ErrorNotExists(Subscriptions)
        if subscription.user_id != user_id or subscription.user_id != data.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Подписка не принадлежит пользователю",
            )
        # Загружаем план
        plan = await self.session.get(Plans, data.plan_id)
        if plan is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="План не найден",
            )
        now_utc = datetime.now(timezone.utc)
        subscription.plan_id = data.plan_id
        subscription.used_checks = 0
        subscription.self_writing = False
        subscription.started_at = now_utc
        subscription.finish_at = now_utc + timedelta(days=plan.expiration_days)
        await self.session.commit()
        # Перезагружаем подписку с планом для ответа
        subscription = await repo.get(data.id)
        return SubscriptionRead.model_validate(subscription)
