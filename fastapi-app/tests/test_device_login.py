"""
Script para probar el login de dispositivos con rompecabezas criptográfico.
Simula al dispositivo generando el puzzle y enviándolo al servidor.

Uso:
    python tests/test_device_login.py
"""

import os
import sys
import hashlib
import hmac
import requests
from base64 import b64encode, b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# Configuración
API_BASE_URL = "http://localhost:8000"  # Ajusta según tu entorno
DEVICE_ID = 5  # ID del dispositivo en la BD
API_KEY = "CFr9woIVKTSQ3YPnwUcYvKOc1FqKx8bi"  # API key del dispositivo

# IMPORTANTE: Esta debe ser la misma encryption_key que tiene el dispositivo en la BD
# En producción, el dispositivo la tiene almacenada de forma segura
DEVICE_ENCRYPTION_KEY = None  # Se obtendrá de la BD o se generará

# La clave del servidor (simulada aquí; en realidad está en el servidor)
# NOTA: En producción, el dispositivo NO conoce server_key, pero la usa implícitamente
# porque el servidor la usó al registrar el dispositivo
# Para esta prueba, necesitamos simular que el dispositivo la conoce
SERVER_KEY_SIMULATED = None  # Se debe obtener del servidor o estar pre-compartida


def cifrar_aes256(data: bytes, key: bytes) -> dict:
    """Cifra datos usando AES-256 en modo CBC."""
    iv = os.urandom(16)  # Vector de inicialización aleatorio
    cipher = AES.new(key, AES.MODE_CBC, iv)
    data_padded = pad(data, AES.block_size)
    ciphertext = cipher.encrypt(data_padded)
    
    return {
        'ciphertext': b64encode(ciphertext).decode('utf-8'),
        'iv': b64encode(iv).decode('utf-8')
    }


def generar_rompecabezas_dispositivo(device_id: int, device_key: bytes, server_key: bytes) -> dict:
    """
    Genera el rompecabezas criptográfico que el dispositivo envía al servidor.
    
    Proceso:
    1. Genera R2 (random de 32 bytes)
    2. Calcula P2 = HMAC-SHA256(device_key + server_key, R2)
    3. Cifra P2 con la device_key
    4. Retorna el puzzle
    """
    ran_dev_1 = os.urandom(32)  # Número aleatorio del dispositivo
    print(f"✓ R2 generado: {b64encode(ran_dev_1).decode('utf-8')[:32]}...")
    
    # Calcular parámetro de identidad
    hmac_key = device_key + server_key
    parametro_id = hmac.new(hmac_key, ran_dev_1, hashlib.sha256).digest()
    print(f"✓ Parámetro de identidad calculado: {b64encode(parametro_id).decode('utf-8')[:32]}...")
    
    # Cifrar parámetro de identidad
    parametro_id_cif = cifrar_aes256(parametro_id, device_key)
    print(f"✓ Parámetro cifrado con clave del dispositivo")
    
    return {
        'id_origen': device_id,
        'Random dispositivo': b64encode(ran_dev_1).decode('utf-8'),
        'Parametro de identidad cifrado': parametro_id_cif
    }


def test_device_login_with_puzzle():
    """Prueba completa del flujo de login con rompecabezas."""
    
    print("\n" + "="*70)
    print("PRUEBA DE LOGIN DE DISPOSITIVO CON ROMPECABEZAS CRIPTOGRÁFICO")
    print("="*70)
    
    # Paso 1: Obtener la encryption_key del dispositivo
    # En un entorno real, el dispositivo ya tiene esta clave almacenada localmente
    # Para esta prueba, necesitamos obtenerla de la BD o generarla
    
    print("\n⚠️  IMPORTANTE:")
    print("   Este script necesita la 'encryption_key' del dispositivo.")
    print("   Opciones:")
    print("   1. Obtenerla de la BD (consulta directa)")
    print("   2. Usar un endpoint admin que la devuelva")
    print("   3. Generarla y registrarla primero")
    print("\n   También necesita la 'server_key' (normalmente pre-compartida)")
    print()
    
    # Simulación: usar claves de ejemplo (CAMBIAR EN PRODUCCIÓN)
    if DEVICE_ENCRYPTION_KEY is None:
        print("⚠️  Usando clave de dispositivo de EJEMPLO (32 bytes)")
        device_key = os.urandom(32)  # En producción: leer de almacenamiento seguro
        print(f"   Key (ejemplo): {b64encode(device_key).decode('utf-8')[:32]}...")
    else:
        device_key = DEVICE_ENCRYPTION_KEY
    
    if SERVER_KEY_SIMULATED is None:
        print("⚠️  Usando server_key de EJEMPLO (32 bytes)")
        server_key = os.urandom(32)  # En producción: pre-compartida
        print(f"   Server Key (ejemplo): {b64encode(server_key).decode('utf-8')[:32]}...")
    else:
        server_key = SERVER_KEY_SIMULATED
    
    print("\n" + "-"*70)
    print("PASO 1: Dispositivo genera el rompecabezas")
    print("-"*70)
    
    puzzle = generar_rompecabezas_dispositivo(DEVICE_ID, device_key, server_key)
    
    print("\n✓ Rompecabezas generado correctamente:")
    print(f"  - id_origen: {puzzle['id_origen']}")
    print(f"  - Random dispositivo: {puzzle['Random dispositivo'][:32]}...")
    print(f"  - Parametro cifrado (ciphertext): {puzzle['Parametro de identidad cifrado']['ciphertext'][:32]}...")
    print(f"  - IV: {puzzle['Parametro de identidad cifrado']['iv'][:32]}...")
    
    print("\n" + "-"*70)
    print("PASO 2: Enviar puzzle al servidor para autenticación")
    print("-"*70)
    
    payload = {
        "device_id": DEVICE_ID,
        "api_key": API_KEY,
        "puzzle_response": puzzle
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/device/login",
            json=payload,
            timeout=10
        )
        
        print(f"\n✓ Respuesta del servidor: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n" + "="*70)
            print("✅ AUTENTICACIÓN EXITOSA")
            print("="*70)
            print(f"Access Token: {data.get('access_token', '')[:50]}...")
            print(f"Token Type: {data.get('token_type')}")
            print(f"Device ID: {data.get('device_id')}")
            print("\n✓ El dispositivo ha sido autenticado correctamente.")
            return True
        else:
            print("\n" + "="*70)
            print("❌ AUTENTICACIÓN FALLIDA")
            print("="*70)
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: No se pudo conectar al servidor")
        print(f"   Verifica que el servidor esté corriendo en {API_BASE_URL}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


def test_simple_without_puzzle():
    """Prueba enviar solo credenciales sin puzzle (debe fallar)."""
    print("\n" + "="*70)
    print("PRUEBA: Login sin puzzle (debe fallar)")
    print("="*70)
    
    payload = {
        "device_id": DEVICE_ID,
        "api_key": API_KEY
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/device/login",
            json=payload,
            timeout=10
        )
        
        print(f"Respuesta: {response.status_code}")
        print(f"Mensaje: {response.text}")
        
        if response.status_code == 400:
            print("\n✓ Correcto: El servidor rechazó el login sin puzzle")
            return True
        else:
            print("\n⚠️  Inesperado: Se esperaba error 400")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


if __name__ == "__main__":
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║   TEST DE AUTENTICACIÓN DE DISPOSITIVOS - ROMPECABEZAS CRYPTO     ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    
    # Mostrar configuración
    print(f"\nConfiguración:")
    print(f"  - API Base URL: {API_BASE_URL}")
    print(f"  - Device ID: {DEVICE_ID}")
    print(f"  - API Key: {API_KEY[:20]}...")
    
    input("\nPresiona ENTER para continuar...")
    
    # Ejecutar pruebas
    # test_simple_without_puzzle()
    # print("\n")
    
    success = test_device_login_with_puzzle()
    
    print("\n")
    if success:
        print("✅ Todas las pruebas completadas exitosamente")
        sys.exit(0)
    else:
        print("❌ Algunas pruebas fallaron")
        print("\n💡 Posibles causas:")
        print("   1. La encryption_key del dispositivo en la BD no coincide")
        print("   2. La server_key usada aquí no coincide con la del servidor")
        print("   3. El dispositivo no existe o el api_key es incorrecto")
        print("   4. El servidor no está corriendo")
        sys.exit(1)
