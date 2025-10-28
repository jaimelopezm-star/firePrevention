from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Any

from api.deps import get_db
from core.security import create_access_token, verify_password
from schemas.auth import UserLogin, DeviceLogin, Token
from models import User, Device, Admin, Manager
from core.decorators import validate_email_decorator, sanitize_input_decorator, async_safe, rate_limit
from core.services import AuthService
from core.utils import ResponseFormatter

router = APIRouter(tags=["Authentication"])

@router.post("/login/user", response_model=Token)
@rate_limit(max_requests=10, time_window=300)  # 10 requests cada 5 minutos
@validate_email_decorator
@sanitize_input_decorator
@async_safe
def login_user(form_data: UserLogin, db: Session = Depends(get_db)) -> Any:
    user = db.query(User).filter(User.email == form_data.email).first()
    if not user or not getattr(user, "pasusuario", None) or not verify_password(form_data.password, user.pasusuario.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Usuario desactivado")

    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": user.email, "type": "user", "id": user.id},
        expires_delta=access_token_expires
    )
    # safe role access
    role_name = None
    if getattr(user, "rol", None) and getattr(user.rol, "name", None):
        role_name = user.rol.name
    elif getattr(user, "admin", None) and getattr(user.admin, "rol", None):
        role_name = getattr(user.admin.rol, "name", None)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "role": role_name
    }


@router.post("/login/admin", response_model=Token)
@rate_limit(max_requests=10, time_window=300)  # 10 requests cada 5 minutos
@validate_email_decorator
@sanitize_input_decorator
@async_safe
def login_admin(form_data: UserLogin, db: Session = Depends(get_db)) -> Any:
    admin = db.query(Admin).filter(Admin.email == form_data.email).first()
    if not admin or not getattr(admin, "pasadmin", None) or not verify_password(form_data.password, admin.pasadmin.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": admin.email, "type": "admin", "id": admin.id},
        expires_delta=access_token_expires
    )
    role_name = getattr(admin, "rol", None)
    role_name = getattr(role_name, "name", None) if role_name else None

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "admin_id": admin.id,
        "role": role_name
    }


@router.post("/login/manager", response_model=Token)
@rate_limit(max_requests=10, time_window=300)  # 10 requests cada 5 minutos
@validate_email_decorator
@sanitize_input_decorator
@async_safe
def login_manager(form_data: UserLogin, db: Session = Depends(get_db)) -> Any:
    manager = db.query(Manager).filter(Manager.email == form_data.email).first()
    if not manager or not getattr(manager, "pasgerente", None) or not verify_password(form_data.password, manager.pasgerente.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": manager.email, "type": "manager", "id": manager.id},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "manager_id": manager.id,
        "role": None
    }

@router.post("/device/login", response_model=Token)
@sanitize_input_decorator
@async_safe
def login_device(device: DeviceLogin, db: Session = Depends(get_db)) -> Any:
    db_device = db.query(Device).filter(Device.id == device.device_id).first()
    if not db_device or not db_device.pasdispositivo or db_device.pasdispositivo.api_key != device.api_key:
        raise HTTPException(status_code=401, detail="Credenciales de dispositivo inválidas")

    access_token_expires = timedelta(minutes=1440)  # 24 horas
    access_token = create_access_token(
        data={"sub": str(db_device.id), "type": "device"},
        expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "device_id": db_device.id
    }