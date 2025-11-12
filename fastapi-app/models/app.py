from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class App(Base):
    __tablename__ = "app"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), index=True)
    version = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    admin_id = Column(Integer, ForeignKey("admin.id"))

    admin = relationship("Admin")
    servicios = relationship("Service", secondary="servicio_app", back_populates="apps")