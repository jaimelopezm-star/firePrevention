from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
from api.v1.routers import auth, users, devices, alerts, sensors
from database.mongo import MongoDBManager, create_indexes
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestión del ciclo de vida de la aplicación.
    
    Startup:
    - Conecta a MongoDB
    - Crea índices en colecciones
    
    Shutdown:
    - Cierra conexión a MongoDB
    """
    # Startup
    try:
        logger.info("🚀 Iniciando aplicación...")
        
        # Conectar a MongoDB
        MongoDBManager.get_client()
        
        # Crear índices
        create_indexes()
        
        logger.info("✅ Aplicación iniciada correctamente")
    except Exception as e:
        logger.error(f"❌ Error en startup: {e}")
    
    yield
    
    # Shutdown
    try:
        logger.info("🔌 Cerrando conexiones...")
        MongoDBManager.close_connection()
        logger.info("✅ Aplicación detenida correctamente")
    except Exception as e:
        logger.error(f"❌ Error en shutdown: {e}")


app = FastAPI(
    title="Fire Prevention System API",
    description="API modularizada para sistema de prevención de incendios con IoT",
    version="2.0.0",
    lifespan=lifespan
)

# Incluir routers
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(users.router, prefix="/api/v1/users")
app.include_router(devices.router, prefix="/api/v1/devices")
app.include_router(sensors.router, prefix="/api/v1")  # Incluye /device/reading y /devices/{id}/readings

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Esquemas de seguridad: uno para usuarios y otro para dispositivos
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token para usuarios, admins y managers"
        },
        "DeviceAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token para dispositivos IoT (POST /device/login)"
        }
    }
    
    # Endpoints que NO requieren autenticación
    no_auth_endpoints = ["login_user", "login_admin", "login_manager", "login_device", 
                         "root", "health_check", "generate_puzzle_for_testing", 
                         "init_device_encryption_key"]
    
    # Endpoints que requieren autenticación de DISPOSITIVO
    device_endpoints = ["/api/v1/device/reading"]
    
    for path, path_item in openapi_schema["paths"].items():
        for operation in path_item.values():
            if isinstance(operation, dict):
                operation_id = operation.get("operationId", "")

                # 1) Endpoints públicos: sin auth explícita
                if operation_id in no_auth_endpoints:
                    continue

                # 2) Endpoints de dispositivo: DeviceAuth siempre
                if path in device_endpoints:
                    operation["security"] = [{"DeviceAuth": []}]
                    if "description" in operation:
                        operation["description"] = f"{operation['description']}\n\n**⚠️ Requiere JWT de DISPOSITIVO** (obtenido con POST /api/v1/auth/login/device)"
                    continue

                # 3) Resto de endpoints: BearerAuth siempre (usuarios/admins/managers)
                #    Forzamos incluso si 'security' existe vacío [] para evitar que Swagger muestre el modal vacío.
                operation["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/")
def root():
    return {"message": "Fire Prevention API v2.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}