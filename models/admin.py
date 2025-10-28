from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Admin(Base):
    __tablename__ = "admin"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), index=True)
    email = Column(String(100), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    rol_id = Column(Integer, ForeignKey("rol.id"))
    pasadmin_id = Column(Integer, ForeignKey("pasadmin.id"))

    rol = relationship("Role")
    managers = relationship("Manager", back_populates="admin")
    #pasadmin = relationship("PasAdmin", back_populates="admin")
    pasadmin = relationship("PasAdmin", uselist=False, back_populates="admin", foreign_keys=[pasadmin_id])