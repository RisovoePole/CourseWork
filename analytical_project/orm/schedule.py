from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from orm.base import Base


class ScheduleORM(Base):
    __tablename__ = "schedule"

    id: Mapped[int] = mapped_column(primary_key=True)

    day_of_week: Mapped[int]
    pair_number: Mapped[int]

    audience_id: Mapped[int] = mapped_column(
        ForeignKey("audience.audience_id")
    )

    discipline_id: Mapped[int] = mapped_column(
        ForeignKey("discipline.discipline_id")
    )

    professor_id: Mapped[int] = mapped_column(
        ForeignKey("professor.professor_id")
    )