from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Device(Base):
    __tablename__ = "dispositivo"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), index=True)
    device_type = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    admin_id = Column(Integer, ForeignKey("admin.id"))
    pasdispositivo_id = Column(Integer, ForeignKey("pasdispositivo.id"))

    admin = relationship("Admin")   
    # disambiguate multiple FK paths by telling SQLAlchemy which local column is the foreign key
    pasdispositivo = relationship(
        "PasDispositivo",
        uselist=False,
        back_populates="device",
        foreign_keys=[pasdispositivo_id]
    )
    servicios = relationship("Service", secondary="servicio_dispositivo", back_populates="dispositivos")
