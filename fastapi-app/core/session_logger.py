"""
Gestor de logging de sesiones en formato CSV.
Thread-safe para uso con múltiples workers de Uvicorn.
"""
import csv
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SessionLogger:
    """
    Servicio para registrar eventos de sesión en un archivo CSV único.
    
    Thread-safe: Usa lock para evitar corrupción cuando múltiples workers
    escriben simultáneamente en el mismo archivo.
    """
    
    _lock = threading.Lock()
    _csv_path = None
    _headers_written = False
    
    # Columnas del CSV
    HEADERS = [
        "timestamp",
        "event",
        "user_id",
        "user_type",
        "email",
        "jti",
        "ip_address",
        "user_agent",
        "expires_at",
        "reason",
        "endpoint"
    ]
    
    @classmethod
    def _get_csv_path(cls) -> Path:
        """Obtiene la ruta del archivo CSV (UN SOLO ARCHIVO)"""
        if cls._csv_path is None:
            # Usar LOGS_DIR de variables de entorno (por defecto /var/log/fastapi)
            import os
            logs_base = Path(os.getenv("LOGS_DIR", "logs"))
            logs_dir = logs_base / "sessions"
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            # UN SOLO ARCHIVO: sessions_history.csv
            cls._csv_path = logs_dir / "sessions_history.csv"
        
        return cls._csv_path
    
    @classmethod
    def _ensure_headers(cls, csv_path: Path) -> None:
        """Asegura que el archivo CSV tenga headers (solo la primera vez)"""
        if not csv_path.exists() or csv_path.stat().st_size == 0:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=cls.HEADERS)
                writer.writeheader()
            logger.info(f"CSV headers creados en {csv_path}")
    
    @classmethod
    def _write_event(cls, event_data: dict) -> None:
        """
        Escribe un evento en el CSV de forma thread-safe.
        
        Args:
            event_data: Diccionario con los campos del evento
        """
        csv_path = cls._get_csv_path()
        
        # Lock para evitar escrituras simultáneas
        with cls._lock:
            try:
                # Asegurar que existan los headers
                cls._ensure_headers(csv_path)
                
                # Escribir evento (append mode)
                with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=cls.HEADERS)
                    writer.writerow(event_data)
                
            except Exception as e:
                logger.error(f"Error escribiendo en CSV de sesiones: {e}")
    
    @classmethod
    def log_login(
        cls,
        user_id: int,
        user_type: str,
        email: str,
        jti: str,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        expires_at: Optional[str] = None
    ) -> None:
        """
        Registra un login exitoso.
        
        Args:
            user_id: ID del usuario/admin/manager/device
            user_type: Tipo de entidad ("user", "admin", "manager", "device")
            email: Email del usuario (vacío para devices)
            jti: JWT ID único del token generado
            ip: Dirección IP del cliente
            user_agent: User-Agent del navegador/dispositivo
            expires_at: Timestamp de expiración del token (ISO 8601)
        """
        event_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "login",
            "user_id": user_id,
            "user_type": user_type,
            "email": email or "",
            "jti": jti,
            "ip_address": ip or "",
            "user_agent": user_agent or "",
            "expires_at": expires_at or "",
            "reason": "",
            "endpoint": ""
        }
        cls._write_event(event_data)
        logger.info(f"Login registrado: {user_type} ID {user_id} desde {ip}")
    
    @classmethod
    def log_login_rejected(
        cls,
        user_id: int,
        user_type: str,
        email: str,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        reason: str = "session_active"
    ) -> None:
        """
        Registra un intento de login rechazado (sesión activa).
        
        Args:
            user_id: ID del usuario/admin/manager/device
            user_type: Tipo de entidad
            email: Email del usuario
            ip: Dirección IP del intento
            user_agent: User-Agent del intento
            reason: Motivo del rechazo (por defecto "session_active")
        """
        event_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "login_rejected",
            "user_id": user_id,
            "user_type": user_type,
            "email": email or "",
            "jti": "",  # No se generó token
            "ip_address": ip or "",
            "user_agent": user_agent or "",
            "expires_at": "",
            "reason": reason,
            "endpoint": ""
        }
        cls._write_event(event_data)
        logger.warning(f"Login rechazado: {user_type} ID {user_id} desde {ip} - {reason}")
    
    @classmethod
    def log_logout(
        cls,
        user_id: int,
        user_type: str,
        jti: str,
        ip: Optional[str] = None,
        reason: str = "manual"
    ) -> None:
        """
        Registra un logout (manual o forzado).
        
        Args:
            user_id: ID del usuario/admin/manager/device
            user_type: Tipo de entidad
            jti: JWT ID del token cerrado
            ip: Dirección IP (opcional, no siempre disponible en logout)
            reason: Motivo ("manual", "forced", "admin")
        """
        event_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "logout",
            "user_id": user_id,
            "user_type": user_type,
            "email": "",
            "jti": jti,
            "ip_address": ip or "",
            "user_agent": "",
            "expires_at": "",
            "reason": reason,
            "endpoint": ""
        }
        cls._write_event(event_data)
        logger.info(f"Logout registrado: {user_type} ID {user_id} - {reason}")
    
    @classmethod
    def log_expired(
        cls,
        user_id: int,
        user_type: str,
        jti: str,
        reason: str = "ttl"
    ) -> None:
        """
        Registra una sesión expirada por TTL de Redis.
        
        Args:
            user_id: ID del usuario
            user_type: Tipo de entidad
            jti: JWT ID del token expirado
            reason: Motivo ("ttl" por defecto)
        """
        event_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "expired",
            "user_id": user_id,
            "user_type": user_type,
            "email": "",
            "jti": jti,
            "ip_address": "",
            "user_agent": "",
            "expires_at": "",
            "reason": reason,
            "endpoint": ""
        }
        cls._write_event(event_data)
        logger.info(f"Sesión expirada: {user_type} ID {user_id} - {reason}")
    
    @classmethod
    def log_request(
        cls,
        user_id: int,
        user_type: str,
        jti: str,
        endpoint: str,
        ip: Optional[str] = None
    ) -> None:
        """
        Registra un request autenticado (opcional, para debugging).
        
        Args:
            user_id: ID del usuario
            user_type: Tipo de entidad
            jti: JWT ID del token usado
            endpoint: Endpoint accedido
            ip: Dirección IP
        """
        event_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "request",
            "user_id": user_id,
            "user_type": user_type,
            "email": "",
            "jti": jti,
            "ip_address": ip or "",
            "user_agent": "",
            "expires_at": "",
            "reason": "",
            "endpoint": endpoint
        }
        cls._write_event(event_data)
