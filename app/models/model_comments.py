from datetime import datetime
import uuid

from sqlalchemy import ARRAY, UUID, Boolean, Column, Float, ForeignKey, Integer, String, Table
from app.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Coordinates(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    comment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("comments.id", ondelete="CASCADE"), nullable=False)
    x1: Mapped[float] = mapped_column(Float, nullable=False)
    y1: Mapped[float] = mapped_column(Float, nullable=False)
    x2: Mapped[float] = mapped_column(Float, nullable=False)
    y2: Mapped[float] = mapped_column(Float, nullable=False)    


class Comments(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    answer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("answers.id", ondelete="CASCADE"), nullable=False)
    answer_file_key: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("comment_types.id"), nullable=False)
    human: Mapped[bool] = mapped_column(Boolean, nullable=False)
    files: Mapped[list[str]] = mapped_column(ARRAY(String()), nullable=True)

    coordinates: Mapped[list["Coordinates"]] = relationship(
        "Coordinates",
        backref="comment",
        cascade="all, delete-orphan",

    )


class CommentTypes(Base):
    __tablename__="comment_types"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    short_name: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)




# Разметку сделать как дополнительную таблицу, потому что может понадобится контекст выделять на нескольких строчках
# Привязать comment types к subjects и по subject_name получать список типов комментов, а потом type в id нужный менять
    # type: str
    # description: str
    # error_word: str
    # error_context: str|None
    # context: bool



# INSERT INTO "public"."comment_types" ("id", "short_name", "name") VALUES
# ('5b7fef30-60d6-40ca-a0d6-3f6a83cbcc4b', 'О',  'Орфографические ошибки'),
# ('13e2f6b9-797a-4d9a-bcbe-643201a30d91', 'М',  'Морфологические ошибки'),
# ('15526401-27df-494b-ae21-7fdfdad6a29e', 'ФГ',  'Фонетико-графические ошибки'),
# ('1bbc3170-0468-4788-a2f4-07e01a22a94e', 'П',  'Пунктуационные ошибки'),
# ('063a9aab-4dc3-4cea-b161-d977da141926', 'Г',  'Грамматические ошибки'),
# ('d3c47d53-7b17-44b2-b26d-63af21dc58d8', 'Р',  'Речевые ошибки');