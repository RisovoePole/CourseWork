# orm/students_group.py
from sqlalchemy import Column, Integer, String
from orm.base import Base


class StudentsGroupORM(Base):
    __tablename__ = "students_group"

    students_group_id = Column(Integer, primary_key=True)
    group_name = Column(String, nullable=False)
    students_count = Column(Integer, nullable=False)