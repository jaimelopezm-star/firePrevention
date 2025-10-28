# models/pas_dispositivo.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class PasDispositivo(Base):
    __tablename__ = "pasdispositivo"
    id = Column(Integer, primary_key=True, index=True)
    api_key = Column(String(100), unique=True, index=True)

    # FK is on dispositivo.pasdispositivo_id; keep relationship back to Device
    device = relationship("Device", back_populates="pasdispositivo")