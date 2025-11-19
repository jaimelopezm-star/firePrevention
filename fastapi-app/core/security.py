from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import uuid
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status
from core.config import settings

logger = logging.getLogger(__name__)

# CAMBIAR A ARGON2 (SIN LÍMITE DE 72 CARACTERES)
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=102400,  # 100 MB
    argon2__time_cost=2,
    argon2__parallelism=8
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if hashed_password is None:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.warning("Password verification failed: %s", e)
        # Fallback para migración (solo si usas texto plano)
        logger.warning("Using plaintext fallback (insecure!)")
        return plain_password == hashed_password

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT con un JTI (JWT ID) único para tracking de sesión.
    
    Args:
        data: Datos a incluir en el token (sub, type, id, etc.)
        expires_delta: Tiempo de expiración del token
    
    Returns:
        Token JWT firmado con JTI único
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    
    # Generar JTI único (JWT ID) para identificar el token en Redis
    jti = str(uuid.uuid4())
    
    to_encode.update({
        "exp": expire,
        "jti": jti,
        "iat": datetime.utcnow()  # Issued at
    })
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> Dict[str, Any]:
    """
    Decodifica y valida un token JWT.
    
    Args:
        token: Token JWT a decodificar
    
    Returns:
        Payload del token decodificado
    
    Raises:
        HTTPException: Si el token es inválido o expiró
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"Token decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

def extract_jti_from_token(token: str) -> str:
    """
    Extrae el JTI de un token JWT sin validar expiración.
    Útil para logging cuando el token ya fue validado.
    
    Args:
        token: Token JWT completo
    
    Returns:
        JTI del token o string vacío si no existe
    """
    try:
        payload = decode_token(token)
        return payload.get("jti", "")
    except:
        return ""