# orm/roomtype.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from orm.base import Base


class RoomTypeORM(Base):
    __tablename__ = "roomtype"

    room_type_id = Column(Integer, primary_key=True)
    room_type_name = Column(String, nullable=False)

    audiences = relationship(
        "AudienceORM",
        secondary="audience_roomtype",
        back_populates="roomtypes"
    )