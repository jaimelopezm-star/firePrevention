from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from api.deps import get_db, get_current_user, require_role
from schemas.user import UserCreate, UserResponse
from models import User, Role, PasUsuario
from core.security import get_password_hash
from core.decorators import validate_email_decorator, sanitize_input_decorator, async_safe, validate_password_decorator
from core.services import UserService
from core.utils import ResponseFormatter

router = APIRouter(tags=["Users"])


@router.get("/me")
@async_safe
def read_users_me(current_user=Depends(get_current_user)):
    return ResponseFormatter.success(current_user, "Perfil obtenido exitosamente")


@router.get("/")
@async_safe
def list_users(
        current_user=Depends(require_role("admin")),
        db: Session = Depends(get_db)
):
    users = db.query(User).all()
    return ResponseFormatter.success(users, "Usuarios listados exitosamente")


@router.post("/")
@validate_email_decorator
@validate_password_decorator  # ← NUEVO decorador de password
@sanitize_input_decorator
@async_safe
def create_user(
        user: UserCreate,
        current_user=Depends(require_role("admin")),
        db: Session = Depends(get_db)
):
    # ✅ SOLO validar si el email ya existe (los decoradores ya validaron formato)
    if db.query(User).filter(User.email == user.email).first():
        return ResponseFormatter.error("Email ya registrado")

    role = db.query(Role).filter(Role.id == user.rol_id).first()
    if not role:
        return ResponseFormatter.error("Rol no encontrado")

    hashed_password = get_password_hash(user.password)
    new_pasusuario = PasUsuario(hashed_password=hashed_password)
    db.add(new_pasusuario)
    db.flush()

    new_user = User(
        nombre=user.nombre,
        email=user.email,
        is_active=user.is_active,
        rol_id=user.rol_id,
        pasusuario_id=new_pasusuario.id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return ResponseFormatter.success(new_user, "Usuario creado exitosamente")