# models/pas_admin.py
from sqlalchemy import Column, Integer, String, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from database import Base

class PasAdmin(Base):
    __tablename__ = "pasadmin"
    id = Column(Integer, primary_key=True, index=True)
    hashed_password = Column(String(255))
    encryption_key = Column(LargeBinary(64))  # VARBINARY(64) para clave AES-256 del rompecabezas

    # The FK is on admin.pasadmin_id; keep relationship back to Admin
    admin = relationship("Admin", back_populates="pasadmin")