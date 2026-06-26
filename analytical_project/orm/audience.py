# orm/audience.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from orm.base import Base


class AudienceORM(Base):
    __tablename__ = "audience"

    audience_id = Column(Integer, primary_key=True)
    room_name = Column(String, nullable=False)
    amount_of_seats = Column(Integer, nullable=False)

    # M:N через association table
    roomtypes = relationship(
        "RoomTypeORM",
        secondary="audience_roomtype",
        back_populates="audiences"
    )