# Sistema de Sesiones Únicas con Redis

## 📋 Resumen

Tu plataforma IoT ahora implementa **sesión única segura** para usuarios, administradores y managers usando Redis. Esto significa:

- ✅ Solo 1 token activo por usuario a la vez
- ✅ Si intentas hacer login con sesión activa → **409 Conflict** (debes hacer logout primero)
- ✅ Logout manual invalida el token inmediatamente (incluso si no expiró)
- ✅ Los tokens robados pueden ser revocados instantáneamente
- ✅ Control total sobre sesiones activas

---

## 🔧 Cambios Implementados

### 1. **RedisManager** (`core/config.py`)
Nuevo gestor de conexión Redis con operaciones de sesión:

```python
RedisManager.save_active_token(user_id, user_type, jti, expires_in)
RedisManager.get_active_token(user_id, user_type)
RedisManager.delete_active_token(user_id, user_type)
RedisManager.is_token_valid(user_id, user_type, jti)
```

**Claves Redis usadas:**
- `session:user:123` → guarda el JTI del token activo del usuario 123
- `session:admin:5` → guarda el JTI del admin 5
- TTL automático = tiempo de expiración del token

---

### 2. **Tokens JWT con JTI** (`core/security.py`)
Cada token ahora incluye un **JTI (JWT ID)** único generado con `uuid.uuid4()`:

```json
{
  "sub": "user@example.com",
  "type": "user",
  "id": 123,
  "exp": 1730000000,
  "iat": 1729996400,
  "jti": "a3f8d9c2-4b7e-4f5a-9c2d-1e8f7a6b5c4d"
}
```

El JTI permite identificar cada token único en Redis.

---

### 3. **SessionService** (`core/services.py`)
Nuevos métodos para gestión de sesiones:

- `check_active_session()`: Lanza 409 si ya hay sesión activa
- `save_session()`: Guarda JTI en Redis al hacer login
- `invalidate_session()`: Elimina JTI de Redis al hacer logout
- `verify_token_session()`: Verifica que el token siga activo

---

### 4. **AuthService actualizado** (`core/services.py`)
El método `auth_by_password()` ahora:

1. Valida credenciales (email + password)
2. **VERIFICA si ya hay sesión activa** → si existe, lanza 409
3. Genera nuevo token JWT con JTI
4. **GUARDA el JTI en Redis** con TTL de 60 minutos
5. Retorna access_token

---

### 5. **Endpoint /logout** (`api/v1/routers/auth.py`)
Nuevo endpoint para cerrar sesión:

```http
POST /logout
Authorization: Bearer <tu_token>
```

**Respuestas:**
- `204 No Content`: Logout exitoso
- `401 Unauthorized`: Token inválido o faltante

Después del logout, el token **ya no funciona** incluso si no expiró.

---

### 6. **Validación de sesión en requests** (`api/deps.py`)
La función `get_current_user_or_device()` ahora:

1. Decodifica el token JWT
2. Extrae el JTI
3. **CONSULTA Redis**: ¿Este JTI es el token activo del usuario?
4. Si NO está en Redis o no coincide → 401 "Sesión inválida o cerrada"

Esto aplica a **todos los endpoints protegidos** que usan `Depends(get_current_user)`.

---

## 🚀 Cómo Probar

### **Escenario 1: Login normal**

```bash
# 1. Hacer login
curl -X POST http://localhost/api/v1/auth/login/user \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "tu_password"}'
```

**Respuesta 200:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user_id": 123,
  "role": "admin"
}
```

✅ El JTI del token se guarda en Redis como `session:user:123`

---

### **Escenario 2: Intento de doble login (sesión activa)**

```bash
# 2. Intentar hacer login de nuevo SIN hacer logout
curl -X POST http://localhost/api/v1/auth/login/user \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "tu_password"}'
```

**Respuesta 409 Conflict:**
```json
{
  "detail": "Ya existe una sesión activa para este user. Debes cerrar sesión primero usando POST /logout"
}
```

❌ **No genera nuevo token** hasta que hagas logout.

---

### **Escenario 3: Logout manual**

```bash
# 3. Hacer logout con el token del paso 1
curl -X POST http://localhost/api/v1/auth/logout \
  -H "Authorization: Bearer eyJhbGc..."
```

**Respuesta 204 No Content** (sin body)

✅ El JTI se elimina de Redis → el token ya no funciona.

---

### **Escenario 4: Usar token después de logout**

```bash
# 4. Intentar usar el token viejo en un endpoint protegido
curl -X GET http://localhost/api/v1/users/me \
  -H "Authorization: Bearer eyJhbGc..."
```

**Respuesta 401:**
```json
{
  "detail": "Sesión inválida o cerrada. Inicia sesión nuevamente."
}
```

❌ Aunque el token no expiró, Redis no lo reconoce como activo.

---

### **Escenario 5: Login después de logout**

```bash
# 5. Ahora puedes hacer login otra vez
curl -X POST http://localhost/api/v1/auth/login/user \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "tu_password"}'
```

**Respuesta 200:** Nuevo token generado y guardado en Redis.

---

## 🔐 Seguridad

### **Ventajas del sistema implementado:**

1. **Protección contra robo de tokens:**
   - Si te roban el token, haces logout y el token robado deja de funcionar.

2. **Control de sesiones concurrentes:**
   - No puedes estar logueado desde 2 dispositivos al mismo tiempo (sesión única).

3. **Auditoría simplificada:**
   - Puedes saber cuántas sesiones activas hay consultando Redis.

4. **Revocación instantánea:**
   - No necesitas esperar a que expire el token (60 min); logout es inmediato.

---

## ⚙️ Configuración Redis

El sistema usa las variables de entorno de tu `docker-compose.yml`:

```env
REDIS_HOST=redis       # Nombre del servicio Docker
REDIS_PORT=6379
REDIS_PASSWORD=tu_password_redis_aqui
```

Si tu Redis no tiene password, el código ya maneja eso (`password=None` si está vacío).

---

## 📊 Monitoreo de Sesiones (opcional)

Puedes agregar un endpoint de administración para ver sesiones activas:

```python
@router.get("/admin/active-sessions")
def list_active_sessions():
    redis_conn = RedisManager.get_connection()
    keys = redis_conn.keys("session:*")
    sessions = []
    for key in keys:
        jti = redis_conn.get(key)
        ttl = redis_conn.ttl(key)
        sessions.append({"key": key, "jti": jti, "ttl_seconds": ttl})
    return {"active_sessions": len(sessions), "sessions": sessions}
```

---

## 🛠️ Despliegue

### **1. Reconstruir contenedor FastAPI**

```powershell
docker compose build fastapi
docker compose up -d fastapi
```

### **2. Verificar que Redis esté corriendo**

```powershell
docker ps | findstr redis
```

### **3. Probar endpoint de logout**

```powershell
# Login
$response = Invoke-RestMethod -Uri "http://localhost/api/v1/auth/login/user" `
  -Method POST -ContentType "application/json" `
  -Body '{"email":"test@example.com","password":"test123"}'

$token = $response.access_token

# Logout
Invoke-RestMethod -Uri "http://localhost/api/v1/auth/logout" `
  -Method POST -Headers @{"Authorization"="Bearer $token"}
```

---

## ⚠️ Notas Importantes

1. **Tokens antiguos sin JTI:**
   - Si tienes tokens generados antes de este cambio, darán error 401 "Token no compatible".
   - Solución: Los usuarios deben hacer login nuevamente.

2. **Dispositivos (devices):**
   - Por ahora, los dispositivos NO usan sesión única (pueden tener múltiples tokens).
   - Si quieres aplicar sesión única a dispositivos, descomenta la validación en `auth_by_puzzle_device()`.

3. **Expiración natural:**
   - Si el token expira (60 min), Redis lo elimina automáticamente por TTL.
   - No necesitas limpiar manualmente.

4. **Reinicio de Redis:**
   - Si Redis se reinicia, todas las sesiones activas se pierden.
   - Los usuarios verán 401 y deberán hacer login nuevamente.

---

## 📝 Resumen del Flujo

```
┌─────────────────────────────────────────────────────┐
│  Usuario intenta LOGIN                              │
└─────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│  ¿Ya tiene sesión activa en Redis?                 │
└─────────────────────────────────────────────────────┘
        │                              │
        │ SÍ                          │ NO
        ▼                              ▼
┌─────────────────┐          ┌─────────────────────────┐
│ 409 CONFLICT    │          │ Generar token JWT       │
│ "Haz logout"    │          │ con JTI único           │
└─────────────────┘          └─────────────────────────┘
                                       │
                                       ▼
                             ┌─────────────────────────┐
                             │ Guardar JTI en Redis    │
                             │ session:user:123 = JTI  │
                             │ TTL = 3600 segundos     │
                             └─────────────────────────┘
                                       │
                                       ▼
                             ┌─────────────────────────┐
                             │ 200 OK + access_token   │
                             └─────────────────────────┘
```

---

## 🎯 Próximos Pasos (Opcional)

1. **Dashboard de sesiones activas:** Panel para administradores que muestre usuarios conectados.
2. **Logout forzado:** Endpoint `/admin/force-logout/{user_id}` para cerrar sesión remota.
3. **Historial de sesiones:** Guardar en MySQL cada login/logout con timestamp e IP.
4. **Notificaciones:** Enviar email cuando se detecta login desde IP nueva.

---

## 📚 Referencias

- [Redis Python Client](https://redis-py.readthedocs.io/)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc7519)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
