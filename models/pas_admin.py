# models/pas_admin.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class PasAdmin(Base):
    __tablename__ = "pasadmin"
    id = Column(Integer, primary_key=True, index=True)
    hashed_password = Column(String(255))

    # The FK is on admin.pasadmin_id; keep relationship back to Admin
    admin = relationship("Admin", back_populates="pasadmin")