from __future__ import annotations

from datetime import datetime, timedelta
import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, func, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.model_users import Users

class Plans(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(True), primary_key=True, index=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    verifications_count: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    expiration_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    refund_limits: Mapped[int] = mapped_column(Integer, nullable=False)

    subscriptions: Mapped[list["Subscriptions"]] = relationship(
        "Subscriptions",
        back_populates="plan"
    )

class Subscriptions(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(True), primary_key=True, index=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("plans.id", ondelete="SET NULL"), nullable=True)
    self_writing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    used_checks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    finish_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["Users"] = relationship(
      "Users",
      backref="subscription"
    )

    plan: Mapped["Plans"] = relationship(
        "Plans",
        back_populates="subscriptions"
    )


class PaymentStatus(str, enum.Enum):
    """Статусы платежа"""
    pending = "pending"
    succeeded = "succeeded"
    canceled = "canceled"
    failed = "failed"



class Payments(Base):
    """Модель платежей"""
    id: Mapped[uuid.UUID] = mapped_column(UUID(True), primary_key=True, index=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    subscription_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # Сумма в рублях
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.pending)
    payment_provider_id: Mapped[str] = mapped_column(String, nullable=True, index=True)  # ID платежа от провайдера (ЮКасса)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

