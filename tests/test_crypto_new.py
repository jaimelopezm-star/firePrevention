from database import SessionLocal
from core.crypto_new import CryptoManager

def test_crypto_new():
    db = SessionLocal()
    try:
        crypto_manager = CryptoManager(db)
        device_id = 7  # ID de un dispositivo existente
        
        print("Probando registro de clave...")
        key = crypto_manager.register_device_key(device_id)
        print(f"✅ Clave registrada: {len(key)} bytes")
        
        print("\nProbando recuperación de clave...")
        retrieved_key = crypto_manager.get_key_by_id(device_id)
        print(f"✅ Clave recuperada: {len(retrieved_key)} bytes")
        print(f"Claves coinciden: {key == retrieved_key}")
        
        print("\nProbando cifrado...")
        test_data = b"Mensaje de prueba"
        encrypted = crypto_manager.cifrar_aes256(test_data, key)
        print(f"✅ Datos cifrados: {encrypted}")
        
        print("\nProbando descifrado...")
        decrypted = crypto_manager.descifrar_aes256(encrypted, key)
        print(f"✅ Datos descifrados: {decrypted.decode('utf-8')}")
        
        print("\nProbando generación de rompecabezas...")
        puzzle = crypto_manager.generar_rompecabezas_dispositivo(device_id, crypto_manager.server_id)
        print(f"✅ Rompecabezas generado: {puzzle}")
        
        print("\nProbando verificación de rompecabezas...")
        result = crypto_manager.verificar_rompecabezas_dispositivo(puzzle)
        print(f"✅ Resultado: {result}")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_crypto_new()