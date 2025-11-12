from sqlalchemy import Column, Integer, String, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from database import Base


class PasUsuario(Base):
    __tablename__ = "pasusuario"

    id = Column(Integer, primary_key=True)
    hashed_password = Column(String(255), nullable=False)
    encryption_key = Column(LargeBinary(64))  # VARBINARY(64) para clave AES-256 del rompecabezas

    # ✅ Relación CORRECTA (User tiene pasusuario_id)
    usuario = relationship("User", back_populates="pasusuario", uselist=False)