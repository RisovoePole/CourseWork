from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Identity
from .base import Base


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(Integer, Identity(always=False), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)