from datetime import datetime
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Enum, Table, func
from sqlalchemy.dialects.postgresql import UUID


import enum

from .base import Base

class RoleUser(str, enum.Enum):
    teacher = "teacher"
    student = "student"
    admin   = "admin"

teachers_students = Table(
    "teachers_students",
    Base.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("teacher_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")),
    Column("student_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")),
    Column("classroom_id", UUID(as_uuid=True), ForeignKey("classrooms.id", ondelete="SET NULL"), nullable=True),
)


class Users(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleUser] = mapped_column(Enum(RoleUser), nullable=False)
    is_verificated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    teachers: Mapped[list["Users"]] = relationship(
        "Users",
        secondary=teachers_students,
        primaryjoin=lambda: Users.id == teachers_students.c.student_id,
        secondaryjoin=lambda: Users.id == teachers_students.c.teacher_id,
        back_populates="students",
    )

    students: Mapped[list["Users"]] = relationship(
        "Users",
        secondary=teachers_students,
        primaryjoin=lambda: Users.id == teachers_students.c.teacher_id,
        secondaryjoin=lambda: Users.id == teachers_students.c.student_id,
        back_populates="teachers",
    )

    classrooms: Mapped[list["Classrooms"]] = relationship(
        "Classrooms",
        backref="teacher",
        cascade="all, delete-orphan",
        passive_deletes=True,
        overlaps="students,teachers",  # Указываем, что это relationship перекрывается с students и teachers
    )