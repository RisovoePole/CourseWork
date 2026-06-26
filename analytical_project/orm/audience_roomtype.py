# orm/audience_roomtype.py
from sqlalchemy import Table, Column, Integer, ForeignKey
from orm.base import Base

audience_roomtype = Table(
    "audience_roomtype",
    Base.metadata,
    Column("room_type_id", Integer, ForeignKey("roomtype.room_type_id"), primary_key=True),
    Column("audience_id", Integer, ForeignKey("audience.audience_id"), primary_key=True),
)