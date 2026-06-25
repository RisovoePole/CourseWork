from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Identity
from .base import Base


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, Identity(always=False), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)