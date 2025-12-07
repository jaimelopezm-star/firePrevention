from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from typing import Any, Optional

from api.deps import get_db
from schemas.auth import UserLogin, DeviceLogin, Token
from models import User, Device, Admin, Manager
from models.pas_dispositivo import PasDispositivo
from core.decorators import (
    rate_limit,
    validate_email_decorator,
    sanitize_input_decorator,
    async_safe,
)
from core.services import AuthService, SessionService
from core.security import decode_token
 

router = APIRouter(tags=["Authentication"])

# Usuario, admin y manager: SIEMPRE por contraseña. Dispositivo: puzzle.

@router.post("/login/user", response_model=Token)
@rate_limit(max_requests=10, time_window=300)
@validate_email_decorator
@sanitize_input_decorator
@async_safe
def login_user(form_data: UserLogin, request: Request, db: Session = Depends(get_db)) -> Any:
    """
    Login de usuario - siempre por contraseña.
    
    ⚠️ SESIÓN ÚNICA: Si ya tienes una sesión activa, este endpoint devolverá 409 Conflict.
    Debes hacer logout primero usando POST /logout con tu token actual.
    """
    return AuthService.auth_by_password(
        User, "user", 
        form_data.email, 
        form_data.password, 
        db,
        request_ip=request.client.host if request.client else None,
        request_user_agent=request.headers.get("user-agent", "")
    )


@router.post("/login/admin", response_model=Token)
@rate_limit(max_requests=10, time_window=300)
@validate_email_decorator
@sanitize_input_decorator
@async_safe
def login_admin(form_data: UserLogin, request: Request, db: Session = Depends(get_db)) -> Any:
    """
    Login de admin - siempre por contraseña.
    
    ⚠️ SESIÓN ÚNICA: Si ya tienes una sesión activa, este endpoint devolverá 409 Conflict.
    Debes hacer logout primero usando POST /logout con tu token actual.
    """
    return AuthService.auth_by_password(
        Admin, "admin", 
        form_data.email, 
        form_data.password, 
        db,
        request_ip=request.client.host if request.client else None,
        request_user_agent=request.headers.get("user-agent", "")
    )


@router.post("/login/manager", response_model=Token)
@rate_limit(max_requests=10, time_window=300)
@validate_email_decorator
@sanitize_input_decorator
@async_safe
def login_manager(form_data: UserLogin, request: Request, db: Session = Depends(get_db)) -> Any:
    """
    Login de manager - siempre por contraseña.
    
    ⚠️ SESIÓN ÚNICA: Si ya tienes una sesión activa, este endpoint devolverá 409 Conflict.
    Debes hacer logout primero usando POST /logout con tu token actual.
    """
    return AuthService.auth_by_password(
        Manager, "manager", 
        form_data.email, 
        form_data.password, 
        db,
        request_ip=request.client.host if request.client else None,
        request_user_agent=request.headers.get("user-agent", "")
    )

@router.post("/device/login", response_model=Token)
@sanitize_input_decorator
@async_safe
def login_device(device: DeviceLogin, request: Request, db: Session = Depends(get_db)) -> Any:
    """
    Login de dispositivo - Siempre usa rompecabezas criptográfico.
    
    ⚠️ SESIÓN ÚNICA: Si el dispositivo ya tiene una sesión activa, devolverá 409 Conflict.
    El dispositivo debe hacer logout primero.
    """
    return AuthService.auth_by_puzzle_device(
        device.device_id, 
        device.api_key, 
        device.puzzle_response, 
        db,
        request_ip=request.client.host if request.client else None,
        request_user_agent=request.headers.get("user-agent", "")
    )


@router.post("/logout", status_code=204)
@async_safe
def logout(request: Request, authorization: Optional[str] = Header(None)):
    """
    Cierra la sesión actual invalidando el token en Redis.
    
    Requiere el token JWT en el header Authorization: Bearer <token>
    
    Devuelve:
    - 204 No Content: Logout exitoso
    - 401 Unauthorized: Token inválido o faltante
    
    Nota: Después del logout, el token ya no podrá usarse para autenticar requests,
    incluso si aún no ha expirado.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autorización requerido",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = authorization.split(" ")[1]
    
    try:
        # Decodificar token para obtener user_id y user_type
        payload = decode_token(token)
        user_id = payload.get("sub")  # El ID está en "sub" no en "id"
        user_type = payload.get("type")
        
        if not user_id or not user_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
        
        # Invalidar sesión en Redis y registrar en CSV
        SessionService.invalidate_session(
            user_id, 
            user_type, 
            reason="manual",
            ip=request.client.host if request.client else None
        )
        
        return  # 204 No Content (sin body)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cerrar sesión: {str(e)}"
        )


# ============================================================================
# ENDPOINTS AUXILIARES PARA PRUEBAS - ELIMINAR EN PRODUCCIÓN
# ============================================================================

@router.post("/device/generate-puzzle-test", tags=["Testing"])
def generate_puzzle_for_testing(device_id: int, db: Session = Depends(get_db)):
    """
    🧪 ENDPOINT DE PRUEBA - Genera un rompecabezas para un dispositivo.
    
    ⚠️ SOLO PARA DESARROLLO/TESTING
    En producción, el DISPOSITIVO genera el puzzle, NO el servidor.
    
    Este endpoint simula lo que haría el dispositivo:
    1. Genera R2 (random)
    2. Calcula HMAC
    3. Cifra con la clave del dispositivo
    4. Devuelve el puzzle listo para copiar en /device/login
    
    Uso en Swagger:
    1. Llama a este endpoint con el device_id
    2. Copia el objeto 'puzzle' de la respuesta
    3. Úsalo en el campo 'puzzle_response' de POST /device/login
    """
    import os
    import hashlib
    import hmac
    from base64 import b64encode
    from core.crypto_new import CryptoManager
    
    # Validar que el dispositivo existe
    db_device = db.query(Device).filter(Device.id == device_id).first()
    if not db_device:
        raise HTTPException(status_code=404, detail=f"Dispositivo con ID {device_id} no encontrado")
    
    # Verificar que tiene pasdispositivo asociado
    if not db_device.pasdispositivo_id:
        raise HTTPException(
            status_code=400, 
            detail=f"Dispositivo {device_id} no tiene pasdispositivo_id. Debe tener un registro en pasdispositivo."
        )
    
    # Obtener el pasdispositivo
    pas_disp = db.query(PasDispositivo).filter(PasDispositivo.id == db_device.pasdispositivo_id).first()
    
    if not pas_disp:
        raise HTTPException(
            status_code=400,
            detail=f"Registro pasdispositivo con ID {db_device.pasdispositivo_id} no encontrado"
        )
    
    crypto_manager = CryptoManager(db)
    
    # Obtener clave del dispositivo
    device_key = crypto_manager.get_key_by_id(device_id)
    if not device_key:
        raise HTTPException(
            status_code=400,
            detail=f"Dispositivo {device_id} no tiene encryption_key. Usa /device/init-encryption-key primero."
        )
    
    # Validar que la clave tenga exactamente 32 bytes (AES-256)
    if len(device_key) != 32:
        raise HTTPException(
            status_code=500,
            detail=f"La encryption_key del dispositivo tiene {len(device_key)} bytes (esperado: 32). "
                   f"Regenera la clave con POST /device/init-encryption-key?device_id={device_id}"
        )
    
    # Simular lo que hace el dispositivo: generar el rompecabezas
    ran_dev = os.urandom(32)  # R2
    hmac_key = device_key + crypto_manager.server_key
    parametro_id = hmac.new(hmac_key, ran_dev, hashlib.sha256).digest()
    parametro_id_cif = crypto_manager.cifrar_aes256(parametro_id, device_key)
    
    puzzle = {
        'id_origen': device_id,
        'Random dispositivo': b64encode(ran_dev).decode('utf-8'),
        'Parametro de identidad cifrado': parametro_id_cif
    }
    
    return {
        "message": "Puzzle generado correctamente. Copia el objeto 'puzzle' y úsalo en POST /device/login",
        "device_id": device_id,
        "api_key": pas_disp.api_key,
        "puzzle": puzzle,
        "instructions": {
            "step_1": "Copia todo el objeto 'puzzle' de arriba",
            "step_2": "Ve a POST /device/login",
            "step_3": "Usa este payload:",
            "payload_example": {
                "device_id": device_id,
                "api_key": pas_disp.api_key,
                "puzzle_response": "<PEGA_AQUI_EL_OBJETO_PUZZLE>"
            }
        }
    }


@router.post("/device/init-encryption-key", tags=["Testing"])
def init_device_encryption_key(device_id: int, db: Session = Depends(get_db)):
    """
    🧪 ENDPOINT DE PRUEBA - Inicializa/regenera la encryption_key de un dispositivo.
    
    ⚠️ SOLO PARA DESARROLLO/TESTING
    
    Genera una nueva encryption_key de 32 bytes para el dispositivo y la guarda en la BD.
    Útil para:
    - Dispositivos nuevos sin clave
    - Reiniciar la clave si hay problemas
    - Preparar dispositivos para pruebas
    
    ADVERTENCIA: Esto invalidará cualquier puzzle anterior generado con la clave vieja.
    """
    from core.crypto_new import CryptoManager
    
    # Validar que el dispositivo existe
    db_device = db.query(Device).filter(Device.id == device_id).first()
    if not db_device:
        raise HTTPException(status_code=404, detail=f"Dispositivo con ID {device_id} no encontrado")
    
    # Verificar que tiene pasdispositivo_id
    if not db_device.pasdispositivo_id:
        raise HTTPException(
            status_code=400,
            detail=f"Dispositivo {device_id} no tiene pasdispositivo_id. Debes crear primero un registro en pasdispositivo y asignarlo."
        )
    
    # Obtener el pasdispositivo
    pas_disp = db.query(PasDispositivo).filter(PasDispositivo.id == db_device.pasdispositivo_id).first()
    
    if not pas_disp:
        raise HTTPException(
            status_code=400,
            detail=f"Registro pasdispositivo con ID {db_device.pasdispositivo_id} no encontrado"
        )
    
    crypto_manager = CryptoManager(db)
    
    # Generar y registrar nueva clave
    try:
        key = crypto_manager.register_device_key(device_id)
        
        return {
            "message": "Encryption key generada y guardada exitosamente",
            "device_id": device_id,
            "key_length": len(key),
            "api_key": pas_disp.api_key,
            "device_info": {
                "nombre": db_device.nombre,
                "device_type": db_device.device_type,
                "pasdispositivo_id": db_device.pasdispositivo_id
            },
            "next_steps": {
                "1": "Usa POST /device/generate-puzzle-test para generar un puzzle",
                "2": "O implementa la generación del puzzle en el dispositivo real"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar clave: {str(e)}")