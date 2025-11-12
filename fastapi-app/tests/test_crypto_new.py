"""
Test completo del sistema de rompecabezas criptográfico para dispositivos.
Simula el flujo correcto: el dispositivo genera el puzzle y el servidor lo verifica.
"""

from database import SessionLocal
from core.crypto_new import CryptoManager
import os
import hashlib
import hmac
from base64 import b64encode
import json


def test_crypto_new():
    """Prueba el flujo completo de crypto para dispositivos."""
    db = SessionLocal()
    try:
        crypto_manager = CryptoManager(db)
        device_id = 5  # ID de un dispositivo existente (AJUSTA según tu BD)
        
        print("="*70)
        print("TEST DE ROMPECABEZAS CRIPTOGRÁFICO PARA DISPOSITIVOS")
        print("="*70)
        
        # Paso 1: Registrar/verificar clave del dispositivo
        print("\n[1/6] Probando registro de clave...")
        key = crypto_manager.register_device_key(device_id)
        print(f"✅ Clave registrada: {len(key)} bytes")
        
        # Paso 2: Recuperar clave
        print("\n[2/6] Probando recuperación de clave...")
        retrieved_key = crypto_manager.get_key_by_id(device_id)
        print(f"✅ Clave recuperada: {len(retrieved_key)} bytes")
        print(f"✅ Claves coinciden: {key == retrieved_key}")
        
        # Paso 3: Probar cifrado/descifrado básico
        print("\n[3/6] Probando cifrado...")
        test_data = b"Mensaje de prueba"
        encrypted = crypto_manager.cifrar_aes256(test_data, key)
        print(f"✅ Datos cifrados correctamente")
        
        print("\n[4/6] Probando descifrado...")
        decrypted = crypto_manager.descifrar_aes256(encrypted, key)
        print(f"✅ Datos descifrados: {decrypted.decode('utf-8')}")
        
        # Paso 4: SIMULAR LO QUE HACE EL DISPOSITIVO (generar puzzle)
        print("\n[5/6] Simulando generación de puzzle por el DISPOSITIVO...")
        print("     (En producción, esto lo hace el dispositivo, NO el servidor)")
        
        # El dispositivo genera R2
        ran_dev = os.urandom(32)
        print(f"     - R2 generado: {b64encode(ran_dev).decode('utf-8')[:32]}...")
        
        # El dispositivo calcula HMAC
        device_key = retrieved_key
        hmac_key = device_key + crypto_manager.server_key
        parametro_id = hmac.new(hmac_key, ran_dev, hashlib.sha256).digest()
        print(f"     - HMAC calculado: {b64encode(parametro_id).decode('utf-8')[:32]}...")
        
        # El dispositivo cifra el parámetro de identidad
        parametro_id_cif = crypto_manager.cifrar_aes256(parametro_id, device_key)
        print(f"     - Parámetro cifrado correctamente")
        
        # El dispositivo construye el puzzle
        puzzle_from_device = {
            'id_origen': device_id,
            'Random dispositivo': b64encode(ran_dev).decode('utf-8'),
            'Parametro de identidad cifrado': parametro_id_cif
        }
        
        print(f"\n✅ Puzzle generado por dispositivo:")
        print(f"   id_origen: {puzzle_from_device['id_origen']}")
        print(f"   Random dispositivo: {puzzle_from_device['Random dispositivo'][:40]}...")
        print(f"   Parametro cifrado: {parametro_id_cif['ciphertext'][:40]}...")
        
        # Paso 5: El servidor verifica el puzzle del dispositivo
        print("\n[6/6] Servidor verificando puzzle del dispositivo...")
        result = crypto_manager.verificar_rompecabezas_dispositivo(puzzle_from_device)
        
        if result['valido']:
            print(f"✅ VERIFICACIÓN EXITOSA")
            print(f"   {result['mensaje']}")
            print(f"   id_origen: {result['id_origen']}")
            print(f"   id_destino: {result['id_destino']}")
        else:
            print(f"❌ VERIFICACIÓN FALLIDA")
            print(f"   Error: {result.get('error')}")
        
        # Generar payload listo para Swagger
        print("\n" + "="*70)
        print("PAYLOAD LISTO PARA SWAGGER/POSTMAN")
        print("="*70)
        
        # Obtener el api_key del dispositivo
        from models import Device
        db_device = db.query(Device).filter(Device.id == device_id).first()
        
        if db_device and db_device.pasdispositivo:
            swagger_payload = {
                "device_id": device_id,
                "api_key": db_device.pasdispositivo.api_key,
                "puzzle_response": puzzle_from_device
            }
            
            print("\nCopia este JSON en Swagger (POST /device/login):")
            print(json.dumps(swagger_payload, indent=2))
            
            # Guardar en archivo
            output_file = "device_login_payload.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(swagger_payload, f, indent=2, ensure_ascii=False)
            print(f"\n✅ Payload guardado en: {output_file}")
        else:
            print("\n⚠️  No se pudo obtener api_key del dispositivo")
            print("   Asegúrate de que el dispositivo existe en la BD con pas_dispositivo")
        
        print("\n" + "="*70)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    test_crypto_new()