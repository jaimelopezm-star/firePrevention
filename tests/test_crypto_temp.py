from database import SessionLocal
from core.crypto import CryptoManager
from models.device import Device
import sys
import importlib

# Forzar la recarga del módulo
import core.crypto
importlib.reload(core.crypto)

def test_crypto():
    db = SessionLocal()
    try:
        # Crear el CryptoManager
        crypto_manager = CryptoManager(db)
        
        # Usar un dispositivo existente (ID 7 según tu imagen)
        device_id = 7
        
        # Registrar una clave para el dispositivo
        try:
            key = crypto_manager.register_device_key(device_id)
            print(f"✅ Clave registrada con éxito para dispositivo {device_id}")
            print(f"Longitud de la clave: {len(key)} bytes")
            
            # Intentar recuperar la clave
            retrieved_key = crypto_manager.get_key_by_id(device_id)
            print(f"✅ Clave recuperada exitosamente")
            print(f"Las claves coinciden: {key == retrieved_key}")
            
            # Probar cifrado
            test_data = b"Prueba de cifrado"
            encrypted = crypto_manager.cifrar_aes256(test_data, key)
            print(f"\n✅ Datos cifrados correctamente:")
            print(encrypted)
            
            # Probar descifrado
            decrypted = crypto_manager.descifrar_aes256(encrypted, key)
            print(f"\n✅ Datos descifrados correctamente:")
            print(decrypted.decode('utf-8'))
            
            # Probar rompecabezas
            puzzle = crypto_manager.generar_rompecabezas_dispositivo(device_id, crypto_manager.server_id)
            print(f"\n✅ Rompecabezas generado:")
            print(puzzle)
            
            # Verificar rompecabezas
            result = crypto_manager.verificar_rompecabezas_dispositivo(puzzle)
            print(f"\n✅ Verificación del rompecabezas:")
            print(result)
            
        except Exception as e:
            print(f"❌ Error durante la prueba: {str(e)}")
            raise e
            
    finally:
        db.close()

if __name__ == "__main__":
    test_crypto()