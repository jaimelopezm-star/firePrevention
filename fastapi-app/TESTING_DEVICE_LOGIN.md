# 🧪 Guía Rápida de Pruebas - Login de Dispositivos

## Métodos para Probar el Rompecabezas Criptográfico

Tienes **3 opciones** para probar el login de dispositivos:

---

## ✅ **OPCIÓN 1: Usar Endpoints Auxiliares en Swagger (MÁS FÁCIL)**

### Paso 1: Inicializar la clave del dispositivo

1. Ve a Swagger: `http://localhost:8000/docs`
2. Busca: `POST /device/init-encryption-key` (etiqueta "Testing")
3. Haz clic en **"Try it out"**
4. Ingresa el `device_id` (ejemplo: `5`)
5. Click en **"Execute"**

**Respuesta esperada:**
```json
{
  "message": "Encryption key generada y guardada exitosamente",
  "device_id": 5,
  "key_length": 32,
  "api_key": "CFr9woIVKTSQ3YPnwUcYvKOc1FqKx8bi"
}
```

### Paso 2: Generar el puzzle

1. Busca: `POST /device/generate-puzzle-test` (etiqueta "Testing")
2. Haz clic en **"Try it out"**
3. Ingresa el mismo `device_id` (ejemplo: `5`)
4. Click en **"Execute"**

**Respuesta esperada:**
```json
{
  "message": "Puzzle generado correctamente...",
  "device_id": 5,
  "api_key": "CFr9woIVKTSQ3YPnwUcYvKOc1FqKx8bi",
  "puzzle": {
    "id_origen": 5,
    "Random dispositivo": "xK9j2Lm4nP8qR7sT...",
    "Parametro de identidad cifrado": {
      "ciphertext": "Hs7dF3k2mQ6vW9yB...",
      "iv": "mP8nQ1zX4cV7bN2k..."
    }
  },
  "instructions": { ... }
}
```

### Paso 3: Usar el puzzle para login

1. **COPIA TODO** el objeto `"puzzle"` de la respuesta anterior
2. Busca: `POST /device/login` (etiqueta "Authentication")
3. Haz clic en **"Try it out"**
4. Pega este JSON (ajustando con tu data):

```json
{
  "device_id": 5,
  "api_key": "CFr9woIVKTSQ3YPnwUcYvKOc1FqKx8bi",
  "puzzle_response": {
    // <-- PEGA AQUÍ EL OBJETO "puzzle" COMPLETO DEL PASO 2
    "id_origen": 5,
    "Random dispositivo": "xK9j2Lm4nP8qR7sT...",
    "Parametro de identidad cifrado": {
      "ciphertext": "Hs7dF3k2mQ6vW9yB...",
      "iv": "mP8nQ1zX4cV7bN2k..."
    }
  }
}
```

5. Click en **"Execute"**

**Respuesta esperada (ÉXITO):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "device_id": 5
}
```

---

## ✅ **OPCIÓN 2: Usar el Script de Test (Python)**

### Ejecutar el test completo:

```powershell
cd "c:\iotServidor Fastapi\version estabe subida al servidor\iot-platform\fastapi-app"

# Activar entorno virtual si lo usas
# .\venv\Scripts\Activate.ps1

# Ejecutar test
python tests\test_crypto_new.py
```

**Este script:**
- ✅ Registra la encryption_key del dispositivo
- ✅ Simula la generación del puzzle por el dispositivo
- ✅ Verifica el puzzle en el servidor
- ✅ Genera un archivo `device_login_payload.json` listo para copiar

**Salida esperada:**
```
======================================================================
TEST DE ROMPECABEZAS CRIPTOGRÁFICO PARA DISPOSITIVOS
======================================================================

[1/6] Probando registro de clave...
✅ Clave registrada: 32 bytes

[2/6] Probando recuperación de clave...
✅ Clave recuperada: 32 bytes
✅ Claves coinciden: True

...

✅ VERIFICACIÓN EXITOSA
   Dispositivo autenticado correctamente

======================================================================
PAYLOAD LISTO PARA SWAGGER/POSTMAN
======================================================================

✅ Payload guardado en: device_login_payload.json

======================================================================
✅ TODAS LAS PRUEBAS COMPLETADAS
======================================================================
```

### Luego usa el JSON generado:

1. Abre el archivo `device_login_payload.json`
2. Copia su contenido
3. Pégalo en Swagger en `POST /device/login`

---

## ✅ **OPCIÓN 3: Requests HTTP (PowerShell/curl)**

### Paso 1: Inicializar clave

```powershell
$baseUrl = "http://localhost:8000"
$deviceId = 5

# Inicializar encryption_key
$response1 = Invoke-RestMethod -Method Post -Uri "$baseUrl/device/init-encryption-key?device_id=$deviceId"
$response1 | ConvertTo-Json
```

### Paso 2: Generar puzzle

```powershell
# Generar puzzle
$response2 = Invoke-RestMethod -Method Post -Uri "$baseUrl/device/generate-puzzle-test?device_id=$deviceId"
$puzzle = $response2.puzzle
$apiKey = $response2.api_key

$response2 | ConvertTo-Json -Depth 5
```

### Paso 3: Login con puzzle

```powershell
# Login
$body = @{
    device_id = $deviceId
    api_key = $apiKey
    puzzle_response = $puzzle
} | ConvertTo-Json -Depth 5

$response3 = Invoke-RestMethod -Method Post -Uri "$baseUrl/device/login" -ContentType "application/json" -Body $body
$response3 | ConvertTo-Json
```

---

## 📋 Prerequisitos

### 1. El dispositivo debe existir en la BD

```sql
SELECT * FROM devices WHERE id = 5;
```

Si no existe, créalo:

```sql
INSERT INTO devices (name, location, type) VALUES ('Sensor Temp 01', 'Planta Baja', 'sensor');
```

### 2. El dispositivo debe tener registro en `pas_dispositivo`

```sql
SELECT * FROM pas_dispositivo WHERE device_id = 5;
```

Si no existe, créalo:

```sql
INSERT INTO pas_dispositivo (device_id, api_key) 
VALUES (5, 'CFr9woIVKTSQ3YPnwUcYvKOc1FqKx8bi');
```

### 3. El dispositivo necesita `encryption_key`

Usa el endpoint `/device/init-encryption-key` o el script `test_crypto_new.py` para generarla.

---

## ⚠️ Notas Importantes

### Sobre `server_key`

La `server_key` se genera **aleatoriamente al iniciar el servidor**. Esto significa:

- ✅ Si usas el endpoint auxiliar: funciona (mismo proceso)
- ⚠️ Si generas el puzzle externamente y luego reinicias el servidor: fallará

**Solución para producción:** Hacer `server_key` fija en el código:

```python
# En core/crypto_new.py, línea ~19
self.server_key = b'tu_clave_fija_de_32_bytes_aqui!'  # Exactamente 32 bytes
```

### Endpoints de Testing

Los endpoints auxiliares (`/device/generate-puzzle-test` y `/device/init-encryption-key`) están marcados con 🧪 y deben:

- ✅ Usarse en desarrollo/testing
- ❌ **Eliminarse o protegerse en producción**

---

## 🐛 Troubleshooting

### Error: "Dispositivo no encontrado"
- Verifica que el `device_id` existe en la tabla `devices`

### Error: "no tiene registro de credenciales"
- El dispositivo necesita un registro en `pas_dispositivo` con `api_key`

### Error: "no tiene encryption_key"
- Ejecuta `POST /device/init-encryption-key` primero

### Error: "Parámetro de identidad no coincide"
- La `server_key` cambió (servidor reiniciado)
- O la `encryption_key` del dispositivo es incorrecta
- Regenera el puzzle con el endpoint auxiliar

### Error: "Credenciales de dispositivo inválidas"
- El `api_key` no coincide con el de la BD
- O el `device_id` no existe

---

## 📚 Archivos Relevantes

- `api/v1/routers/auth.py` - Endpoints de login y auxiliares
- `core/crypto_new.py` - Lógica del rompecabezas
- `core/services.py` - Servicio de autenticación
- `tests/test_crypto_new.py` - Script de prueba completo
- `DEVICE_AUTH_PUZZLE.md` - Documentación técnica detallada

---

## ✅ Flujo Recomendado para Primera Prueba

1. **Ejecuta el script**: `python tests\test_crypto_new.py`
2. **Revisa la salida** para confirmar que todo funciona
3. **Copia el JSON** del archivo `device_login_payload.json`
4. **Prueba en Swagger**: `POST /device/login` con ese JSON
5. **Deberías recibir** un `access_token` válido

¡Eso es todo! 🎉
