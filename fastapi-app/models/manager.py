from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Manager(Base):
    __tablename__ = "gerente"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), index=True)
    email = Column(String(100), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # ✅ Según tu BD, Manager tiene admin_id y pasgerente_id
    admin_id = Column(Integer, ForeignKey("admin.id"))
    pasgerente_id = Column(Integer, ForeignKey("pasgerente.id"))
    # ✅ Añadimos rol_id para que los managers participen del sistema de permisos
    rol_id = Column(Integer, ForeignKey("rol.id"), nullable=True)

    # ✅ Relaciones CORRECTAS según tu BD
    admin = relationship("Admin", back_populates="managers")
    pasgerente = relationship("PasGerente", back_populates="gerente")
    rol = relationship("Role")

    # ❌ ELIMINAR - Manager NO tiene user_id en tu BD
    # user_id = Column(Integer, ForeignKey("usuario.id"))
    # user = relationship("User", back_populates="gerente")
