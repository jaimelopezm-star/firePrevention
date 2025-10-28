# models/permission.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base  # ✅ ESTA LÍNEA ES OBLIGATORIA
from models.relationships import rol_permiso

class Permission(Base):  # ← Hereda de Base
    __tablename__ = "permiso"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    roles = relationship("Role", secondary=rol_permiso, back_populates="permissions")