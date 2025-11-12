from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from api.v1.routers import auth, users, devices, alerts

app = FastAPI(
    title="Fire Prevention System API",
    description="API modularizada para sistema de prevención de incendios",
    version="2.0.0"
)

app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(users.router, prefix="/api/v1/users")
app.include_router(devices.router, prefix="/api/v1/devices")

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            if "security" not in operation and operation.get("operationId") not in ["login_user", "login_device"]:
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