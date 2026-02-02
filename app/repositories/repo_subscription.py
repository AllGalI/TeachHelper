from typing import Optional, Sequence
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.model_subscription import Subscriptions, Plans


class RepoSubscription:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, subscription: Subscriptions) -> Subscriptions:
        """Создание новой подписки"""
        self.session.add(subscription)
        return subscription

    async def get(self, subscription_id: uuid.UUID) -> Optional[Subscriptions]:
        """Получение подписки по ID с загрузкой связанных данных"""
        stmt = (
            select(Subscriptions)
            .where(Subscriptions.id == subscription_id)
            .options(selectinload(Subscriptions.plan))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[Subscriptions]:
        """Получение активной подписки пользователя (проверка по finish_at)."""
        stmt = (
            select(Subscriptions)
            .where(
                and_(
                    Subscriptions.user_id == user_id,
                    Subscriptions.finish_at > datetime.now(timezone.utc)
                )
            )
            .options(selectinload(Subscriptions.plan))
            .order_by(Subscriptions.started_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id_any(self, user_id: uuid.UUID) -> Optional[Subscriptions]:
        """Получение подписки пользователя без проверки активности (одна запись на пользователя)."""
        stmt = (
            select(Subscriptions)
            .where(Subscriptions.user_id == user_id)
            .options(selectinload(Subscriptions.plan))
            .order_by(Subscriptions.started_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email_hash(self, email_hash: str) -> Optional[Subscriptions]:
        """Получение подписки по хэшу email."""
        stmt = (
            select(Subscriptions)
            .where(Subscriptions.email_hash == email_hash)
            .options(selectinload(Subscriptions.plan))
            .order_by(Subscriptions.started_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user_id(self, user_id: uuid.UUID) -> Sequence[Subscriptions]:
        """Получение всех подписок пользователя."""
        stmt = (
            select(Subscriptions)
            .where(Subscriptions.user_id == user_id)
            .options(selectinload(Subscriptions.plan))
            .order_by(Subscriptions.started_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
