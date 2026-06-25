from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, Integer, BigInteger, Identity
from .base import Base


class Curriculum(Base):
    __tablename__ = "curriculum"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=False), primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)
    lecture_hours_per_week: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    seminar_hours_per_week: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lab_hours_per_week: Mapped[int] = mapped_column(Integer, nullable=False, default=0)