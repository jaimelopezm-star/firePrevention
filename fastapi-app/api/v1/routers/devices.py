from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import secrets

from api.deps import get_db, require_permission
from core.utils import ResponseFormatter
from models import Device, PasDispositivo, Admin
from schemas.device import DeviceCreate, DeviceResponse

router = APIRouter(tags=["Devices"])


@router.post("/", response_model=None)
def create_device(
    payload: DeviceCreate,
    current_admin=Depends(require_permission("create_device")),
    db: Session = Depends(get_db)
):
    """
    Crear un dispositivo IoT.

    Requiere permiso `create_device`. Crea fila en `pasdispositivo` con api_key autogenerado
    y encryption_key, enlazando al admin propietario.
    """
    # Restringir a admin_master únicamente
    try:
        role_name = getattr(getattr(current_admin, "rol", None), "nombre", None)
    except Exception:
        role_name = None
    if role_name != "admin_master":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo admin_master puede crear dispositivos")

    # Validar admin
    admin = db.query(Admin).filter(Admin.id == payload.admin_id).first()
    if not admin:
        return ResponseFormatter.error("Admin no encontrado")

    # Crear pasdispositivo con api_key autogenerado y encryption_key para AES-256
    pas = PasDispositivo()
    # Generar encryption_key de 32 bytes (256 bits para AES-256)
    pas.encryption_key = secrets.token_bytes(32)
    db.add(pas)
    db.flush()

    device = Device(
        nombre=payload.nombre,
        device_type=payload.device_type,
        is_active=payload.is_active,
        admin_id=payload.admin_id,
        pasdispositivo_id=pas.id
    )
    db.add(device)
    db.commit()
    db.refresh(device)

    return ResponseFormatter.success(device, "Dispositivo creado exitosamente")
