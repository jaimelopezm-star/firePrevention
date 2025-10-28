from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from core.validators import Validators
from models import User, Device


class AuthService:
    """Servicios reutilizables para autenticación"""

    @staticmethod
    def validate_user_credentials(db: Session, email: str, password: str, password_hashed: str) -> User:
        """Valida credenciales de usuario de forma segura"""
        user = db.query(User).filter(User.email == email).first()
        if not user or not getattr(user, "pasusuario", None):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        from core.security import verify_password
        if not verify_password(password, user.pasusuario.hashed_password):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        if not user.is_active:
            raise HTTPException(status_code=400, detail="Usuario desactivado")

        return user

    @staticmethod
    def validate_device_credentials(db: Session, device_id: int, api_key: str) -> Device:
        """Valida credenciales de dispositivo"""
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device or not device.pasdispositivo or device.pasdispositivo.api_key != api_key:
            raise HTTPException(status_code=401, detail="Credenciales de dispositivo inválidas")
        return device


class UserService:
    """Servicios para gestión de usuarios"""

    @staticmethod
    def validate_new_user(db: Session, email: str, password: str):
        """Valida datos para nuevo usuario"""
        if not Validators.validate_email(email):
            raise HTTPException(status_code=400, detail="Formato de email inválido")

        if not Validators.validate_password_strength(password):
            raise HTTPException(
                status_code=400,
                detail="La contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula y un número"
            )

        if db.query(User).filter(User.email == email).first():
            raise HTTPException(status_code=400, detail="Email ya registrado")