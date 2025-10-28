from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base
from models.relationships import rol_permiso


class Role(Base):
    __tablename__ = "rol"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)  # ← nullable=False agregado

    # Relación muchos a muchos con Permission (ESTÁ BIEN)
    permissions = relationship(
        "Permission",
        secondary=rol_permiso,
        back_populates="roles"
    )

    # Agregar esta relación para conectar con User
    usuarios = relationship("User", back_populates="rol")