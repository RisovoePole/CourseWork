from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import SmallInteger, Integer, Identity
from .base import Base


class TimeSlot(Base):
    __tablename__ = "time_slots"

    id: Mapped[int] = mapped_column(Integer, Identity(always=False), primary_key=True)
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    slot_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)