from sqlalchemy.orm import Mapped, mapped_column, relationship

from orm.base import Base


class ProfessorORM(Base):
    __tablename__ = "professor"

    professor_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    disciplines = relationship(
        "DisciplineORM",
        secondary="professor_discipline",
        back_populates="professors"
    )