# api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from jose import jwt

from database import get_db
from models import User, Device, PasUsuario, PasDispositivo, Admin, Manager, Role
from models.permission import Permission
from models.relationships import rol_permiso
from core.config import settings
from core.security import verify_password, decode_token
from core.services import SessionService

security = HTTPBearer()


def get_current_user_or_device(
        credentials=Depends(security),
        db: Session = Depends(get_db)
):
    """
    Dependencia de FastAPI que valida tokens JWT y verifica sesión activa en Redis.
    
    IMPORTANTE: Ahora valida que el token esté activo en Redis (no revocado por logout).
    Si el token fue invalidado mediante /logout, esta función rechaza el request.
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decodificar token JWT (valida firma y expiración)
        payload = decode_token(token)
        
        sub = payload.get("sub")
        token_type = payload.get("type")
        user_id = payload.get("id")
        jti = payload.get("jti")
        
        if not jti:
            # Token antiguo sin JTI (generado antes de implementar sesiones)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token no compatible con sistema de sesiones. Inicia sesión nuevamente."
            )
        
        # *** VALIDAR QUE EL TOKEN ESTÉ ACTIVO EN REDIS ***
        # Validamos sesiones para todos los tipos, incluyendo 'device'.
        # Nota: para usuarios/admins/managers usamos el claim 'id',
        # pero para dispositivos el claim 'sub' contiene el device_id.
        user_id_for_session = None
        if token_type == "device":
            # 'sub' fue creado como el device.id en el flujo de login de dispositivos
            user_id_for_session = int(sub) if sub is not None else None
        else:
            # usuarios/admins/managers usan el claim 'id'
            user_id_for_session = user_id

        # Si no tenemos un id válido para comparar en Redis, rechazamos
        if user_id_for_session is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o incompleto (sin id)",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Verificamos que el JTI coincida con la sesión activa en Redis
        if not SessionService.verify_token_session(user_id_for_session, token_type, jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sesión inválida o cerrada. Inicia sesión nuevamente.",
                headers={"WWW-Authenticate": "Bearer"}
            )

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

    except HTTPException:
        raise
    except Exception as e:
        raise credentials_exception


def get_current_user(credentials=Depends(security), db: Session = Depends(get_db)):
    result = get_current_user_or_device(credentials=credentials, db=db)
    if result["type"] != "user":
        raise HTTPException(status_code=403, detail="Solo usuarios pueden acceder")
    return result["data"]


def get_current_device(credentials=Depends(security), db: Session = Depends(get_db)):
    result = get_current_user_or_device(credentials=credentials, db=db)
    if result["type"] != "device":
        raise HTTPException(status_code=403, detail="Solo dispositivos pueden acceder")
    return result["data"]


def require_role(role_name: str):
    def role_checker(current_user=Depends(get_current_user)):
        if current_user.rol.name != role_name:
            raise HTTPException(status_code=403, detail=f"Requiere rol: {role_name}")
        return current_user

    return role_checker


def require_permission(permission_name: str):
    """
    Valida que el principal autenticado (usuario/admin/manager) posea el permiso solicitado.

    Permite granularidad por permisos usando las tablas `rol`, `permiso`, `rol_permiso`.
    """
    def permission_checker(
        principal=Depends(get_current_user_or_device),
        db: Session = Depends(get_db)
    ):
        principal_type = principal["type"]
        principal_obj = principal["data"]

        # Dispositivos no participan en permisos de administración
        if principal_type == "device":
            raise HTTPException(status_code=403, detail="No autorizado (solo usuarios/admins/managers)")

        # Resolver rol según el tipo
        rol_id = getattr(principal_obj, "rol_id", None)
        if not rol_id:
            raise HTTPException(status_code=403, detail="Principal sin rol asignado")

        # Verificar si el rol tiene el permiso solicitado
        has_perm = (
            db.query(Permission)
            .join(rol_permiso, rol_permiso.c.permiso_id == Permission.id)
            .filter(rol_permiso.c.role_id == rol_id, Permission.name == permission_name)
            .first()
        )

        if not has_perm:
            raise HTTPException(status_code=403, detail=f"Permiso requerido: {permission_name}")

        return principal_obj

    return permission_checker