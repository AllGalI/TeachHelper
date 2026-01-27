import enum
import uuid
from sqlalchemy import UUID, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class StatusAnswerFile(str, enum.Enum):
  draft = 'draft'
  pending = 'pending'
  verification = 'verification'
  verified = 'verified'
  banned = 'banned'

class AnswerFiles(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    answer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("answers.id", ondelete="CASCADE"), nullable=False)
    key: Mapped[str] = mapped_column(String, nullable=False)
    ai_status: Mapped[StatusAnswerFile] = mapped_column(Enum(StatusAnswerFile), nullable=False, default=StatusAnswerFile.draft)

