# api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from jose import jwt

from database import get_db
from models import User, Device, PasUsuario, PasDispositivo, Admin, Manager
from core.config import settings
from core.security import verify_password

security = HTTPBearer()


def get_current_user_or_device(
        credentials=Depends(security),
        db: Session = Depends(get_db)
):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub = payload.get("sub")
        token_type = payload.get("type")

        if token_type == "user":
            # Buscar usuario por email (asumiendo que 'sub' es el email)
            user = db.query(User).filter(User.email == sub).first()
            if not user or not user.is_active:
                raise credentials_exception
            # Verificar que tenga pasusuario
            if not user.pasusuario:
                raise credentials_exception
            return {"type": "user", "data": user}

        elif token_type == "admin":
            admin = db.query(Admin).filter(Admin.email == sub).first()
            if not admin:
                raise credentials_exception
            if not getattr(admin, "pasadmin", None):
                raise credentials_exception
            return {"type": "admin", "data": admin}

        elif token_type == "manager":
            manager = db.query(Manager).filter(Manager.email == sub).first()
            if not manager:
                raise credentials_exception
            if not getattr(manager, "pasgerente", None):
                raise credentials_exception
            return {"type": "manager", "data": manager}

        elif token_type == "device":
            # Buscar dispositivo por ID
            device = db.query(Device).filter(Device.id == int(sub)).first()
            if not device or not device.is_active:
                raise credentials_exception
            # Verificar que tenga pasdispositivo
            if not device.pasdispositivo:
                raise credentials_exception
            return {"type": "device", "data": device}

        else:
            raise credentials_exception

    except Exception:
        raise credentials_exception


def get_current_user(db: Session = Depends(get_db)):
    result = get_current_user_or_device(db=db)
    if result["type"] != "user":
        raise HTTPException(status_code=403, detail="Solo usuarios pueden acceder")
    return result["data"]


def get_current_device(db: Session = Depends(get_db)):
    result = get_current_user_or_device(db=db)
    if result["type"] != "device":
        raise HTTPException(status_code=403, detail="Solo dispositivos pueden acceder")
    return result["data"]


def require_role(role_name: str):
    def role_checker(current_user=Depends(get_current_user)):
        if current_user.rol.name != role_name:
            raise HTTPException(status_code=403, detail=f"Requiere rol: {role_name}")
        return current_user

    return role_checker