from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status

from core.config import settings

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verificar una contraseña usando passlib. Si la verificación genera una excepción 
    (por ejemplo, porque el valor almacenado no es un hash válido), recurrir a una comparación directa.
    Esta alternativa no es segura y solo sirve para facilitar 
    la migración desde contraseñas almacenadas en texto plano. Se registra una advertencia al usar esta alternativa.
    """
    if hashed_password is None:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Log the full exception for diagnostics
        import sys
        import traceback

        tb = traceback.format_exc()
        logger.warning("Password verification failed with exception: %s", tb)

        # Try to inspect the bcrypt module used by passlib to give more debugging hints
        try:
            import bcrypt as _bcrypt
            bcrypt_info = {
                "file": getattr(_bcrypt, "__file__", None),
                "attrs": sorted([a for a in dir(_bcrypt) if not a.startswith("__")])[:50],
            }
            logger.warning("bcrypt module info: %s", bcrypt_info)
        except Exception as _e:
            logger.warning("Failed to inspect bcrypt module: %s", _e)

        # Fallback: allow direct comparison if DB has plaintext (migration help)
        logger.warning("Password verification fallback used: stored password may be plaintext")
        return plain_password == hashed_password

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)