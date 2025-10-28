from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class PasUsuario(Base):
    __tablename__ = "pasusuario"

    id = Column(Integer, primary_key=True)
    hashed_password = Column(String(255), nullable=False)

    # ✅ Relación CORRECTA (User tiene pasusuario_id)
    usuario = relationship("User", back_populates="pasusuario", uselist=False)