from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from api.deps import get_db, get_current_user, require_permission
from schemas.user import UserCreate, UserResponse, ManagerCreate, ManagerResponse
from models import User, Role, PasUsuario, Manager, PasGerente, Admin
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
    current_user=Depends(require_permission("view_all_users")),
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
    current_user=Depends(require_permission("create_user")),
        db: Session = Depends(get_db)
):
    """
    Crear un nuevo usuario regular.
    
    **Requiere rol admin.**
    
    **Proceso:**
    1. Valida email único
    2. Verifica que el rol exista
    3. Encripta contraseña con **Argon2** (no bcrypt)
    4. Crea registro en pasusuario
    5. Crea registro en usuario
    """
    # ✅ SOLO validar si el email ya existe (los decoradores ya validaron formato)
    if db.query(User).filter(User.email == user.email).first():
        return ResponseFormatter.error("Email ya registrado")

    role = db.query(Role).filter(Role.id == user.rol_id).first()
    if not role:
        return ResponseFormatter.error("Rol no encontrado")

    # Encriptar con Argon2
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

    return ResponseFormatter.success(new_user, "Usuario creado exitosamente con Argon2")


# Endpoint para crear managers (requiere permiso específico)
@router.post("/manager")
@validate_email_decorator
@validate_password_decorator
@sanitize_input_decorator
@async_safe
def create_manager(
        manager: ManagerCreate,
        current_user=Depends(require_permission("create_manager")),
        db: Session = Depends(get_db)
):
    """
    Crear un nuevo gerente/manager.
    
    **Requiere permiso create_manager.**
    
    **Proceso:**
    1. Valida email único
    2. Verifica que el admin_id exista
    3. Encripta contraseña con **Argon2**
    4. Crea registro en pasgerente
    5. Crea registro en gerente
    """
    # Validar email único
    if db.query(Manager).filter(Manager.email == manager.email).first():
        return ResponseFormatter.error("Email ya registrado para manager")

    # Resolver admin_id: usar el proporcionado o el del usuario actual si es admin
    admin_id_resolved = None
    try:
        # Si viene un admin_id válido (>0), úsalo
        if getattr(manager, "admin_id", None) and manager.admin_id > 0:
            admin_id_resolved = manager.admin_id
        else:
            # Si no viene, intenta usar el id del usuario actual si es Admin
            # current_user puede ser un dict o un ORM dependiendo de ResponseFormatter/serialización
            current_id = getattr(current_user, "id", None) or (current_user.get("id") if isinstance(current_user, dict) else None)
            # Verificar que exista y que pertenezca a la tabla Admin
            if current_id:
                admin_obj = db.query(Admin).filter(Admin.id == current_id).first()
                if admin_obj:
                    admin_id_resolved = admin_obj.id
        
        # Validar que el admin exista finalmente
        admin = db.query(Admin).filter(Admin.id == admin_id_resolved).first() if admin_id_resolved else None
        if not admin:
            return ResponseFormatter.error("Admin no encontrado")
    except Exception:
        return ResponseFormatter.error("Admin no encontrado")

    # Encriptar contraseña con Argon2
    hashed_password = get_password_hash(manager.password)
    new_pasgerente = PasGerente(hashed_password=hashed_password)
    db.add(new_pasgerente)
    db.flush()

    # Crear manager
    # Rol por defecto para gerentes (si existe)
    default_manager_role = db.query(Role).filter(Role.nombre == 'manager').first()

    new_manager = Manager(
        nombre=manager.nombre,
        email=manager.email,
        admin_id=admin_id_resolved,
        pasgerente_id=new_pasgerente.id
    )
    if default_manager_role:
        new_manager.rol_id = default_manager_role.id
    db.add(new_manager)
    db.commit()
    db.refresh(new_manager)

    return ResponseFormatter.success(new_manager, "Manager creado exitosamente con Argon2")
