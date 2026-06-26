# orm/professor_discipline.py
from sqlalchemy import Table, Column, Integer, ForeignKey
from orm.base import Base


professor_discipline = Table(
    "professor_discipline",
    Base.metadata,
    Column("professor_id", Integer, ForeignKey("professor.professor_id"), primary_key=True),
    Column("discipline_id", Integer, ForeignKey("discipline.discipline_id"), primary_key=True),
)