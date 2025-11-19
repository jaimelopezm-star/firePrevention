# ============================================================================
# Dockerfile - FastAPI para Plataforma IoT
# ============================================================================
# Imagen base: Python 3.11 slim (menor superficie de ataque)
FROM python:3.11-slim

# Metadatos
LABEL maintainer="tu_email@ejemplo.com"
LABEL description="FastAPI para plataforma IoT - Proyecto Máster Ciberseguridad"
LABEL version="2.0"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Crear usuario no-root para ejecutar la aplicación
RUN groupadd -r fastapi && useradd -r -g fastapi fastapi

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements e instalar dependencias Python (con caché de Docker)
COPY --chown=fastapi:fastapi requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de aplicación
COPY --chown=fastapi:fastapi . .

# Crear directorios de logs (ANTES de cambiar a usuario no-root)
RUN mkdir -p /var/log/fastapi/sessions && chown -R fastapi:fastapi /var/log/fastapi

# Cambiar a usuario no-root
USER fastapi

# Exponer puerto interno (no accesible desde fuera de Docker)
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Comando de inicio con Uvicorn (producción)
# Logs en /var/log/fastapi/ (montado desde host)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000", "--workers", "2", "--access-log", "--log-level", "info", "--proxy-headers"]