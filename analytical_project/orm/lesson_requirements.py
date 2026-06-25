from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, String, Integer, BigInteger, Identity
from .base import Base


class LessonRequirement(Base):
    __tablename__ = "lesson_requirements"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=False), primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), nullable=False)
    lesson_type: Mapped[str] = mapped_column(String(20), nullable=False)
    required_room_type: Mapped[str] = mapped_column(String(20), nullable=False)
    lessons_per_week: Mapped[int] = mapped_column(Integer, nullable=False)