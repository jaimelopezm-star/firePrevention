from sqlalchemy import Column, Integer, ForeignKey, DateTime, Table
from datetime import datetime
from database import Base

# Tablas intermedias (muchos a muchos)

rol_permiso = Table(
    "rol_permiso",
    Base.metadata,
    Column("rol_id", Integer, ForeignKey("rol.id"), primary_key=True),
    Column("permiso_id", Integer, ForeignKey("permiso.id"), primary_key=True),
    Column("created_at", DateTime, default=datetime.utcnow)
)

usuario_servicio = Table(
    "usuario_servicio",
    Base.metadata,
    Column("usuario_id", Integer, ForeignKey("usuario.id"), primary_key=True),
    Column("servicio_id", Integer, ForeignKey("servicio.id"), primary_key=True),
    Column("fecha_asignacion", DateTime, default=datetime.utcnow)
)

servicio_dispositivo = Table(
    "servicio_dispositivo",
    Base.metadata,
    Column("servicio_id", Integer, ForeignKey("servicio.id"), primary_key=True),
    Column("dispositivo_id", Integer, ForeignKey("dispositivo.id"), primary_key=True),
    Column("fecha_asignacion", DateTime, default=datetime.utcnow)
)

servicio_app = Table(
    "servicio_app",
    Base.metadata,
    Column("servicio_id", Integer, ForeignKey("servicio.id"), primary_key=True),
    Column("app_id", Integer, ForeignKey("app.id"), primary_key=True),
    Column("fecha_asignacion", DateTime, default=datetime.utcnow)
)