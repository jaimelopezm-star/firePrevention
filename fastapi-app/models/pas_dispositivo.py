# models/pas_dispositivo.py
from sqlalchemy import Column, Integer, String, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
import secrets
import string
from database import Base

class PasDispositivo(Base):
    __tablename__ = "pasdispositivo"
    id = Column(Integer, primary_key=True, index=True)
    api_key = Column(String(100), unique=True, index=True)
    encryption_key = Column(LargeBinary(64))  # VARBINARY(64) para clave AES-256

    # FK is on dispositivo.pasdispositivo_id; keep relationship back to Device
    device = relationship("Device", back_populates="pasdispositivo")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.api_key:
            # Generar un API key aleatorio si no se proporciona uno
            alphabet = string.ascii_letters + string.digits
            self.api_key = ''.join(secrets.choice(alphabet) for _ in range(32))