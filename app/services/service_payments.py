import uuid
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from yookassa import Configuration, Payment

from app.config.config_app import settings
from app.exceptions.responses import ErrorNotExists, ErrorRolePermissionDenied
from app.models.model_subscription import PaymentStatus, Payments, Plans, Subscriptions
from app.models.model_users import RoleUser, Users
from app.schemas.schema_payments import (
    PaymentsCreate,
    YooKassaPaymentObject,
    YooKassaRefundObject,
    YooKassaWebhookNotification,
)
from app.services.service_base import ServiceBase
from app.utils.logger import logger


class ServicePayments(ServiceBase):
    async def create(self, data: PaymentsCreate, user: Users):
        """
        Создание платежа через ЮКассу для подписки.
        
        Проверяет, что пользователь - учитель, получает информацию о подписке и плане,
        настраивает ЮКассу и создает платеж.
        """
        try:
            # Проверка, что пользователь - учитель
            if user.role is not RoleUser.teacher:
                raise ErrorRolePermissionDenied(RoleUser.teacher, user.role)

            
            # Получение подписки с планом
            stmt = (
                select(Subscriptions)
                .where(Subscriptions.user_id == user.id)
            )

            subscription = await self.session.scalar(stmt)
            
            # Проверка существования подписки
            if subscription is None:
                raise ErrorNotExists(Subscriptions)
            
            # Настройка конфигурации ЮКассы
            Configuration.account_id = settings.UKASSA_SHOP_ID
            Configuration.secret_key = settings.UKASSA_SECRET_KEY
            
            # Получение суммы платежа из плана и преобразование в строку с двумя знаками после запятой
            plan_orm = await self.session.get(Plans, data.plan_id)
            if plan_orm.name == "Пробный":
                raise HTTPException(403, "Пробный план можно использовать только один раз")

            payment_amount = plan_orm.amount
            payment_value = f"{payment_amount:.2f}"
            
            # Создание платежа через ЮКассу
            # Генерируем internal_payment_id для использования в metadata
            internal_payment_id = uuid.uuid4()
            
            # Добавляем metadata с subscription_id и internal_payment_id для удобства поиска при обработке webhook
            yookassa_payment = Payment.create({
                "amount": {
                    "value": payment_value,
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": f"{settings.FRONT_URL}/plans"
                },
                "capture": True,
                "description": f"Оплата подписки {plan_orm.name}",
                "metadata": {
                    "subscription_id": str(subscription.id),
                    "plan_id": str(plan_orm.id),
                    "internal_payment_id": str(internal_payment_id)
                }
            }, internal_payment_id)
            
            # Сохраняем платеж в БД
            payment_db = Payments(
                id=internal_payment_id,
                user_id=user.id,
                plan_id=plan_orm.id,
                subscription_id=subscription.id,
                amount=payment_amount,  # Сумма в рублях
                status=PaymentStatus.pending,
                payment_provider_id=yookassa_payment.id,  # ID платежа от ЮКассы
            )
            self.session.add(payment_db)
            await self.session.commit()

            return yookassa_payment
            
        except (ErrorRolePermissionDenied, ErrorNotExists) as exc:
            # Пробрасываем HTTP исключения без изменений
            raise
            
        except Exception as exc:
            # Логируем и обрабатываем неожиданные ошибки
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при создании платежа"
            )

    async def handle_webhook(self, notification: YooKassaWebhookNotification):
        """
        Обработка webhook уведомлений от ЮКассы.
        
        Обрабатывает следующие события:
        - payment.succeeded: успешный платеж - обновление подписки
        - payment.waiting_for_capture: платеж ожидает подтверждения - обновление подписки
        - payment.canceled: отмена платежа - обновление статуса платежа
        """
        try:
            event = notification.event
            obj = notification.object
            print(f"event - - {event}")
            
            # Обработка событий платежа
            if event in ["payment.succeeded", "payment.waiting_for_capture"]:
                # Проверяем, что объект - это платеж
                if isinstance(obj, YooKassaPaymentObject):
                    await self._handle_payment_success(obj)
                else:
                    logger.error(f"Ожидался YooKassaPaymentObject для события {event}, получен другой тип")
            elif event == "payment.canceled":
                # Проверяем, что объект - это платеж
                if isinstance(obj, YooKassaPaymentObject):
                    await self._handle_payment_canceled(obj)
                else:
                    logger.error(f"Ожидался YooKassaPaymentObject для события {event}, получен другой тип")
            else:
                # Неизвестное событие - логируем, но не падаем
                logger.warning(f"Неизвестное событие webhook: {event}")

        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            # Не пробрасываем исключение, чтобы вернуть 200 OK для ЮКассы
            # ЮКасса будет повторять запрос, если не получит 200 OK
    
    async def _handle_payment_success(self, payment_object: YooKassaPaymentObject):
        """
        Обработка успешного платежа или платежа, ожидающего подтверждения.
        
        Алгоритм:
        1. Найти payment по payment_provider_id ИЛИ internal_payment_id из metadata
        2. Проверить что status ещё не succeeded (идемпотентность)
        3. Обновить payment.status = succeeded
        4. Найти subscription_id
        5. Обновить подписку: продлить дату, увеличить лимиты
        6. Закоммитить транзакцию
        """
        payment_provider_id = payment_object.id
        internal_payment_id = None
        
        # Получаем internal_payment_id из metadata, если есть
        if payment_object.metadata and "internal_payment_id" in payment_object.metadata:
            try:
                internal_payment_id = uuid.UUID(payment_object.metadata["internal_payment_id"])
            except (ValueError, TypeError):
                logger.warning(f"Не удалось распарсить internal_payment_id из metadata для платежа {payment_provider_id}")
        
        # Шаг 1: Найти payment по payment_provider_id ИЛИ internal_payment_id
        payment = None
        if internal_payment_id:
            # Сначала пытаемся найти по internal_payment_id
            payment = await self.session.get(Payments, internal_payment_id)

        if payment is None:
            # Если не нашли по internal_payment_id, ищем по payment_provider_id
            stmt = (
                select(Payments)
                .where(Payments.payment_provider_id == payment_provider_id)
            )
            payment = await self.session.scalar(stmt)
        
        if payment is None:
            logger.warning(f"Платеж не найден по payment_provider_id={payment_provider_id} или internal_payment_id={internal_payment_id}")
            return
        
        # Шаг 2: Проверить что status ещё не succeeded (идемпотентность)
        if payment.status == PaymentStatus.succeeded:
            logger.info(f"Платеж {payment.id} уже обработан (status=succeeded), пропускаем обработку")
            return
        
        # Шаг 3: Обновить payment.status = succeeded
        payment.status = PaymentStatus.succeeded
        
        # Шаг 4: Найти subscription_id
        if payment.subscription_id is None:
            logger.warning(f"У платежа {payment.id} нет subscription_id")
            await self.session.commit()
            return
        
        subscription = await self.session.get(Subscriptions, payment.subscription_id)
        
        if subscription is None:
            logger.warning(f"Подписка {payment.subscription_id} не найдена")
            await self.session.commit()
            return


        # Шаг 5: Обновить подписку: продлить дату, увеличить лимиты, указать план id из платежа
        now_utc = datetime.now(timezone.utc)

        # План подписки обновлён, начинаем новый период
        subscription.plan_id = payment.plan_id
        subscription.started_at = now_utc
        subscription.finish_at = now_utc + timedelta(days=30)

        # Увеличиваем лимиты: добавляем verifications_count из плана
        subscription.used_checks = 0
        # Если used_checks становится отрицательным, устанавливаем в 0

        # Шаг 6: Закоммитить транзакцию
        await self.session.commit()
        logger.info(
            f"Платеж {payment.id} успешно обработан. Подписка {subscription.id} обновлена: "
            f"finish_at={subscription.finish_at}, used_checks={subscription.used_checks}"
        )
    
    async def _handle_payment_canceled(self, payment_object: YooKassaPaymentObject):
        """
        Обработка отмененного платежа.
        
        Логика:
        - Найти payment по payment_provider_id ИЛИ internal_payment_id из metadata
        - Обновить payment.status = canceled
        - Ничего не делать с подпиской
        - Закоммитить транзакцию
        """
        payment_provider_id = payment_object.id
        internal_payment_id = None
        
        # Получаем internal_payment_id из metadata, если есть
        if payment_object.metadata and "internal_payment_id" in payment_object.metadata:
            try:
                internal_payment_id = uuid.UUID(payment_object.metadata["internal_payment_id"])
            except (ValueError, TypeError):
                logger.warning(f"Не удалось распарсить internal_payment_id из metadata для платежа {payment_provider_id}")
        
        # Найти payment по payment_provider_id ИЛИ internal_payment_id
        payment = None
        if internal_payment_id:
            # Сначала пытаемся найти по internal_payment_id
            payment = await self.session.get(Payments, internal_payment_id)
        
        if payment is None:
            # Если не нашли по internal_payment_id, ищем по payment_provider_id
            stmt = (
                select(Payments)
                .where(Payments.payment_provider_id == payment_provider_id)
            )
            payment = await self.session.scalar(stmt)
        
        if payment is None:
            logger.warning(f"Платеж не найден по payment_provider_id={payment_provider_id} или internal_payment_id={internal_payment_id}")
            return
        
        # Обновить payment.status = canceled
        payment.status = PaymentStatus.canceled
        
        # Ничего не делаем с подпиской, только обновляем статус платежа
        await self.session.commit()
        logger.info(f"Платеж {payment.id} отменен, статус обновлен на canceled")