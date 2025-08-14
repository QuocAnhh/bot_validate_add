from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Numeric

Base = declarative_base()

class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trip_id = Column(String(64), unique=True, index=True, nullable=False)
    provider = Column(String(255), nullable=False)
    origin = Column(String(255), nullable=False)
    destination = Column(String(255), nullable=False)
    origin_city = Column(String(100), nullable=False, index=True)
    destination_city = Column(String(100), nullable=False, index=True)
    departure_time = Column(DateTime, nullable=False)
    price_vnd = Column(Integer, nullable=False) 