import os
from dotenv import load_dotenv
import redis
from typing import Optional

load_dotenv()

class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "j8KmLpQwRtYzXvBnMqWdEaSfGhJkPcVbNlZx")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    # Configuración Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    
    # Configuración MongoDB
    MONGO_HOST: str = os.getenv("MONGO_HOST", "localhost")
    MONGO_PORT: int = int(os.getenv("MONGO_PORT", 27017))
    MONGO_USER: str = os.getenv("MONGO_USER", "admin")
    MONGO_PASSWORD: str = os.getenv("MONGO_PASSWORD", "")
    MONGO_DATABASE: str = os.getenv("MONGO_DATABASE", "iot_sensors")
    MONGO_AUTH_SOURCE: str = os.getenv("MONGO_AUTH_SOURCE", "admin")

settings = Settings()


class RedisManager:
    """Gestor de conexión y operaciones Redis para sesiones de usuario"""
    
    _instance: Optional[redis.Redis] = None
    
    @classmethod
    def get_connection(cls) -> redis.Redis:
        """Obtiene o crea una conexión Redis (singleton)"""
        if cls._instance is None:
            cls._instance = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True,  # Retorna strings en lugar de bytes
                socket_connect_timeout=5,
                socket_timeout=5
            )
        return cls._instance
    
    @classmethod
    def save_active_token(cls, user_id: int, user_type: str, jti: str, expires_in: int) -> None:
        """
        Guarda el token activo de un usuario en Redis.
        
        Args:
            user_id: ID del usuario
            user_type: Tipo de usuario ("user", "admin", "manager", "device")
            jti: ID único del JWT
            expires_in: Tiempo de expiración en segundos
        """
        redis_conn = cls.get_connection()
        key = f"session:{user_type}:{user_id}"
        redis_conn.setex(key, expires_in, jti)
    
    @classmethod
    def get_active_token(cls, user_id: int, user_type: str) -> Optional[str]:
        """
        Obtiene el JTI del token activo de un usuario.
        
        Returns:
            JTI del token activo o None si no hay sesión activa
        """
        redis_conn = cls.get_connection()
        key = f"session:{user_type}:{user_id}"
        return redis_conn.get(key)
    
    @classmethod
    def delete_active_token(cls, user_id: int, user_type: str) -> None:
        """
        Elimina el token activo de un usuario (logout).
        """
        redis_conn = cls.get_connection()
        key = f"session:{user_type}:{user_id}"
        redis_conn.delete(key)
    
    @classmethod
    def is_token_valid(cls, user_id: int, user_type: str, jti: str) -> bool:
        """
        Verifica si un token JTI es el token activo del usuario.
        
        Returns:
            True si el token es válido y activo, False en caso contrario
        """
        active_jti = cls.get_active_token(user_id, user_type)
        return active_jti == jti if active_jti else False