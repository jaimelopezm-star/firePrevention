# models/pas_gerente.py
from sqlalchemy import Column, Integer, String, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from database import Base

class PasGerente(Base):
    __tablename__ = "pasgerente"
    id = Column(Integer, primary_key=True, index=True)
    hashed_password = Column(String(255))
    encryption_key = Column(LargeBinary(64))  # VARBINARY(64) para clave AES-256 del rompecabezas

    # FK is on gerente.pasgerente_id; keep relationship back to Manager
    gerente = relationship("Manager", back_populates="pasgerente")