import uuid
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from app.models.model_users import Users, teachers_students

from .base import Base

class Classrooms(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))


    students: Mapped[list["Users"]] = relationship(
        "Users",
        secondary=teachers_students,
        primaryjoin=lambda: Classrooms.id == teachers_students.c.classroom_id,
        secondaryjoin=lambda: teachers_students.c.student_id == Users.id,
        viewonly=True,  # Только для чтения, так как связь управляется через teachers_students
        overlaps="students,teachers,classrooms",  # Указываем, что это relationship перекрывается с relationships из Users
        # Не используем backref, так как Users.classrooms уже настроен правильно
    )

