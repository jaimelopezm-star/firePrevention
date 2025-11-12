# Autenticación de Dispositivos con Rompecabezas Criptográfico

## Descripción del Flujo

La autenticación de dispositivos utiliza un **rompecabezas criptográfico** para demostrar que el dispositivo posee la clave de cifrado correcta sin transmitirla.

### Flujo Completo

```
┌─────────────┐                                    ┌─────────────┐
│ Dispositivo │                                    │   Servidor  │
└──────┬──────┘                                    └──────┬──────┘
       │                                                  │
       │  1. Generar R2 (random 32 bytes)                │
       │     Calcular P2 = HMAC(key_device+key_server,R2)│
       │     Cifrar P2 con key_device → P2c              │
       │                                                  │
       │  2. POST /device/login                          │
       │     { device_id, api_key, puzzle_response }     │
       ├─────────────────────────────────────────────────>│
       │                                                  │
       │                                   3. Validar     │
       │                                      device_id + │
       │                                      api_key     │
       │                                                  │
       │                                   4. Reconstruir│
       │                                      P2 usando R2│
       │                                                  │
       │                                   5. Descifrar  │
       │                                      P2c con     │
       │                                      key_device  │
       │                                                  │
       │                                   6. Comparar   │
       │                                      P2 == P2c  │
       │                                                  │
       │  7. { access_token, device_id }                 │
       │<─────────────────────────────────────────────────┤
       │                                                  │
```

## Componentes Criptográficos

### Claves involucradas

1. **`encryption_key` (key_device)**: 32 bytes, única por dispositivo
   - Almacenada en `PasDispositivo.encryption_key` 
   - El dispositivo la tiene almacenada localmente de forma segura
   
2. **`server_key`**: 32 bytes, generada al iniciar el servidor
   - Solo existe en memoria del servidor
   - Usada para derivar HMAC
   
3. **`api_key`**: String único por dispositivo
   - Para validación inicial de identidad
   - Almacenado en `PasDispositivo.api_key`

### Algoritmos

- **HMAC-SHA256**: Para generar el parámetro de identidad
- **AES-256-CBC**: Para cifrar el parámetro de identidad
- **Base64**: Para codificar datos binarios en JSON

## Formato del Puzzle

El dispositivo genera y envía este JSON:

```json
{
  "id_origen": 5,
  "Random dispositivo": "base64_encoded_32_bytes",
  "Parametro de identidad cifrado": {
    "ciphertext": "base64_encoded_aes_ciphertext",
    "iv": "base64_encoded_16_bytes_iv"
  }
}
```

### Campos

- **`id_origen`**: ID del dispositivo en la base de datos
- **`Random dispositivo`**: R2 en base64 (32 bytes aleatorios generados por el dispositivo)
- **`Parametro de identidad cifrado`**: P2c cifrado con AES-256-CBC
  - `ciphertext`: P2 cifrado (donde P2 = HMAC-SHA256(key_device + server_key, R2))
  - `iv`: Vector de inicialización usado en AES

## Endpoint: POST /device/login

### Request Body (DeviceLogin)

```json
{
  "device_id": 5,
  "api_key": "CFr9woIVKTSQ3YPnwUcYvKOc1FqKx8bi",
  "puzzle_response": {
    "id_origen": 5,
    "Random dispositivo": "xK9j2Lm4...(base64)...",
    "Parametro de identidad cifrado": {
      "ciphertext": "Hs7dF3k2...(base64)...",
      "iv": "mP8nQ1zX...(base64)..."
    }
  }
}
```

### Response (Token)

#### Éxito (200 OK)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "device_id": 5
}
```

#### Error: Sin puzzle (400 Bad Request)
```json
{
  "detail": "Se requiere puzzle_response. El dispositivo debe generar y enviar el rompecabezas criptográfico."
}
```

#### Error: Credenciales inválidas (401 Unauthorized)
```json
{
  "detail": "Credenciales de dispositivo inválidas"
}
```

#### Error: Puzzle inválido (401 Unauthorized)
```json
{
  "detail": "Parámetro de identidad no coincide - Dispositivo NO autenticado"
}
```

## Código del Dispositivo (Python)

### Generar el Puzzle

```python
import os
import hashlib
import hmac
from base64 import b64encode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

def cifrar_aes256(data: bytes, key: bytes) -> dict:
    """Cifra datos usando AES-256 en modo CBC."""
    iv = os.urandom(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    data_padded = pad(data, AES.block_size)
    ciphertext = cipher.encrypt(data_padded)
    
    return {
        'ciphertext': b64encode(ciphertext).decode('utf-8'),
        'iv': b64encode(iv).decode('utf-8')
    }

def generar_puzzle_dispositivo(device_id: int, device_key: bytes, server_key: bytes) -> dict:
    """
    Genera el rompecabezas criptográfico.
    
    Args:
        device_id: ID del dispositivo en la BD
        device_key: encryption_key del dispositivo (32 bytes)
        server_key: clave del servidor (32 bytes, pre-compartida)
    
    Returns:
        dict: Puzzle listo para enviar al servidor
    """
    # 1. Generar número aleatorio
    ran_dev = os.urandom(32)
    
    # 2. Calcular HMAC
    hmac_key = device_key + server_key
    parametro_id = hmac.new(hmac_key, ran_dev, hashlib.sha256).digest()
    
    # 3. Cifrar parámetro de identidad
    parametro_id_cif = cifrar_aes256(parametro_id, device_key)
    
    # 4. Construir puzzle
    return {
        'id_origen': device_id,
        'Random dispositivo': b64encode(ran_dev).decode('utf-8'),
        'Parametro de identidad cifrado': parametro_id_cif
    }
```

### Enviar al Servidor

```python
import requests

# Configuración
DEVICE_ID = 5
API_KEY = "CFr9woIVKTSQ3YPnwUcYvKOc1FqKx8bi"
DEVICE_KEY = b'...'  # 32 bytes desde almacenamiento seguro
SERVER_KEY = b'...'  # 32 bytes pre-compartida
API_URL = "http://localhost:8000/device/login"

# Generar puzzle
puzzle = generar_puzzle_dispositivo(DEVICE_ID, DEVICE_KEY, SERVER_KEY)

# Enviar al servidor
response = requests.post(API_URL, json={
    "device_id": DEVICE_ID,
    "api_key": API_KEY,
    "puzzle_response": puzzle
})

if response.status_code == 200:
    token = response.json()['access_token']
    print(f"✓ Autenticado. Token: {token[:50]}...")
else:
    print(f"✗ Error: {response.text}")
```

## Pruebas en Swagger

### Paso 1: Generar el Puzzle

Ejecuta el script generador:

```powershell
python fastapi-app/tests/generate_device_puzzle.py
```

Este script usa tu código original (`rompecabezas.py`) y genera el JSON completo.

### Paso 2: Copiar el JSON

El script te dará algo como:

```json
{
  "device_id": 5,
  "api_key": "CFr9woIVKTSQ3YPnwUcYvKOc1FqKx8bi",
  "puzzle_response": {
    "id_origen": "ID_sensor_temperatura",
    "Random dispositivo": "xK9j2Lm4nP8qR7sT...",
    "Parametro de identidad cifrado": {
      "ciphertext": "Hs7dF3k2mQ6vW9yB...",
      "iv": "mP8nQ1zX4cV7bN2k..."
    }
  }
}
```

### Paso 3: Usar en Swagger

1. Abre: `http://localhost:8000/docs`
2. Busca: `POST /device/login`
3. Clic en **"Try it out"**
4. **Pega el JSON** en el campo "Request body"
5. **IMPORTANTE**: Ajusta `device_id` al ID real en tu BD
6. **IMPORTANTE**: Ajusta `api_key` al valor real del dispositivo
7. Clic en **"Execute"**

### Resultado Esperado

✅ **Éxito (200)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "device_id": 5
}
```

## Seguridad

### Fortalezas

✅ **Demuestra posesión de clave**: El dispositivo debe tener `encryption_key` para generar P2 correcto  
✅ **No transmite claves**: Solo envía R2 en claro y P2 cifrado  
✅ **Usa HMAC**: Combina clave del dispositivo y del servidor  
✅ **AES-256**: Cifrado fuerte del parámetro de identidad  

### Consideraciones

⚠️ **Replay attacks**: Añadir timestamp o nonce en futuras versiones  
⚠️ **Server key**: Se genera en memoria al iniciar. Reiniciar invalida puzzles previos  
⚠️ **Pre-compartir server_key**: Debe estar sincronizada entre servidor y dispositivos  

## Comparación con Usuarios

| Aspecto | Usuarios/Admin/Manager | Dispositivos |
|---------|------------------------|--------------|
| Método | Contraseña (argon2) | Rompecabezas criptográfico |
| Validación | verify_password() | HMAC + AES verify |
| Token TTL | 60 minutos | 1440 minutos (24h) |
| Endpoint | `/login/user`, `/login/admin`, `/login/manager` | `/device/login` |
| Generador | N/A | Dispositivo genera puzzle |

## Troubleshooting

### Error: "Key del dispositivo no encontrada"

**Causa**: El dispositivo no tiene `encryption_key` en la BD  
**Solución**: 
```python
from core.crypto_new import CryptoManager
crypto = CryptoManager(db)
key = crypto.register_device_key(device_id)  # Genera y guarda
```

### Error: "Parámetro de identidad no coincide"

**Causas posibles**:
1. `server_key` del dispositivo no coincide con la del servidor
2. `encryption_key` incorrecta
3. Servidor reiniciado entre generación y verificación del puzzle

**Solución**: 
- Verificar que el dispositivo usa la `server_key` correcta
- Confirmar que `encryption_key` en BD coincide con la del dispositivo

### Error: "Se requiere puzzle_response"

**Causa**: Intentaste login sin enviar el puzzle  
**Solución**: El dispositivo **SIEMPRE** debe generar y enviar `puzzle_response`

## Scripts de Utilidad

- `tests/generate_device_puzzle.py`: Genera puzzle para Swagger
- `tests/test_device_login.py`: Prueba completa del flujo (requiere requests)

## Referencias

- `core/crypto_new.py`: Implementación de CryptoManager
- `core/services.py`: AuthService.auth_by_puzzle_device()
- `api/v1/routers/auth.py`: Endpoint /device/login
- `schemas/auth.py`: Modelos DeviceLogin y Token
