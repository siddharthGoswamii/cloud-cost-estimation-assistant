from sqlalchemy import Column, Integer, String, Float
from database import Base

class CloudService(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) # e.g., EC2
    default_config = Column(String) # e.g., t3.medium
    hourly_rate = Column(Float) # e.g., 0.0416