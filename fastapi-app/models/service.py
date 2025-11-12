from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Service(Base):
    __tablename__ = "servicio"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), index=True)
    version = Column(String(20))
    descripcion = Column(Text)
    url = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    admin_id = Column(Integer, ForeignKey("admin.id"))
    gerente_id = Column(Integer, ForeignKey("gerente.id"))

    admin = relationship("Admin")
    gerente = relationship("Manager")
    dispositivos = relationship("Device", secondary="servicio_dispositivo", back_populates="servicios")
    apps = relationship("App", secondary="servicio_app", back_populates="servicios")