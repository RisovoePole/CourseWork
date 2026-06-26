# orm/discipline.py
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from orm.base import Base


class DisciplineORM(Base):
    __tablename__ = "discipline"

    discipline_id = Column(Integer, primary_key=True)
    discipline_name = Column(String, nullable=False)

    optimal_room_type = Column(ARRAY(Integer))

    course_hours = Column(Float, nullable=False)
    seminar_hours = Column(Float, nullable=False)
    lab_hours = Column(Float, nullable=False)

    professors = relationship(
        "ProfessorORM",
        secondary="professor_discipline",
        back_populates="disciplines"
    )