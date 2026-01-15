from datetime import datetime
import uuid

from sqlalchemy import ARRAY, UUID, DateTime, ForeignKey, Integer, String, UniqueConstraint
from app.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Можно сделать так, чтобы учитель сам заполнял критерии, можно сделать так, чтобы критерии были из ЕГЭ
class Criterions(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    exercise_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(), nullable=False)
    score: Mapped[int] = mapped_column(Integer(), nullable=False)


class Exercises(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(), nullable=False)
    description: Mapped[str] = mapped_column(String())
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    files: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=[])

    criterions: Mapped[list["Criterions"]] = relationship(
        "Criterions",
        backref="exercise",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )




class Tasks(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(), nullable=False)
    description: Mapped[str] = mapped_column(String())
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint('name', 'subject_id', 'teacher_id', name='_name_subject_teacher_uc'),
    )

    teacher: Mapped["Users"] = relationship(
        "Users",
        backref="tasks")

    exercises: Mapped[list["Exercises"]] = relationship(
        "Exercises",
        backref="task",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    
    works: Mapped[list["Works"]] = relationship(
        "Works",
        backref="task",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )




