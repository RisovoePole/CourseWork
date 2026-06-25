from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, Integer, BigInteger, Identity
from .base import Base


class ScheduledLesson(Base):
    __tablename__ = "scheduled_lessons"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=False), primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("algorithm_runs.id", ondelete="CASCADE"), nullable=False)
    lesson_requirement_id: Mapped[int] = mapped_column(ForeignKey("lesson_requirements.id"), nullable=False)
    time_slot_id: Mapped[int] = mapped_column(ForeignKey("time_slots.id"), nullable=False)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False)