from datetime import datetime
import enum
import uuid

from sqlalchemy import ARRAY, UUID, Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Table
from app.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship

class StatusWork(str, enum.Enum):
    draft        = "draft"
    inProgress   = "inProgress"
    verification = "verification"
    verificated  = "verificated"
    canceled     = "canceled"

class Assessments(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    answer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("answers.id", ondelete="CASCADE"), nullable=False)
    criterion_id:  Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("criterions.id", ondelete="CASCADE"), nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    criterion: Mapped["Criterions"] = relationship(
        "Criterions",
        backref='assessment'
    )


class Answers(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    work_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("works.id", ondelete="CASCADE"), nullable=False)
    exercise_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("exercises.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(String, default='')
    general_comment: Mapped[str] = mapped_column(String, default='')
    file_keys: Mapped[list[str]] = mapped_column(ARRAY(String()), nullable=True)

    exercise: Mapped["Exercises"] = relationship("Exercises", backref="answer")
    work: Mapped["Works"] = relationship("Works", back_populates="answers")
    assessments: Mapped[list["Assessments"]] = relationship(
        "Assessments",
        backref="answer",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    
    comments: Mapped[list["Comments"]] = relationship(
        "Comments",
        backref="answer",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


class Works(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    finish_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    status: Mapped[StatusWork] = mapped_column(Enum(StatusWork), default=StatusWork.draft, nullable=False)
    сonclusion: Mapped[str] = mapped_column(String, nullable=True)
    ai_verificated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    answers: Mapped[list["Answers"]] = relationship(
        "Answers",
        back_populates="work",
        cascade="all, delete-orphan",
        passive_deletes=True,

    )



