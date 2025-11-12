from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
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
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)