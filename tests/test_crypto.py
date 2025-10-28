from database import SessionLocal
from core.crypto import CryptoManager
from models.device import Device
from models.pas_dispositivo import PasDispositivo

def test_crypto_functions():
    # Crear una sesión de base de datos
    db = SessionLocal()
    test_device = None
    try:
        # Crear el CryptoManager
        crypto_manager = CryptoManager(db)

        # Crear un dispositivo de prueba
        test_device = Device(
            nombre="Dispositivo de Prueba",
            device_type="sensor_temperatura"
        )
        db.add(test_device)
        db.commit()
        db.refresh(test_device)

        print(f"Dispositivo creado con ID: {test_device.id}")

        # Registrar una clave para el dispositivo
        key = crypto_manager.register_device_key(test_device.id)
        print(f"Clave registrada con éxito, longitud: {len(key)} bytes")
        print(f"API Key generado: {test_device.pasdispositivo.api_key}")

        # Verificar que podemos recuperar la clave
        retrieved_key = crypto_manager.get_key_by_id(test_device.id)
        print(f"Clave recuperada con éxito, longitud: {len(retrieved_key)} bytes")
        print(f"Las claves coinciden: {key == retrieved_key}")

        # Probar el cifrado
        test_data = b"Datos de prueba para cifrar"
        encrypted = crypto_manager.cifrar_aes256(test_data, key)
        print(f"\nDatos cifrados: {encrypted}")

        # Probar el descifrado
        decrypted = crypto_manager.descifrar_aes256(encrypted, key)
        print(f"Datos descifrados: {decrypted.decode('utf-8')}")

        # Probar el rompecabezas criptográfico
        puzzle = crypto_manager.generar_rompecabezas_dispositivo(test_device.id, crypto_manager.server_id)
        print(f"\nRompecabezas generado: {puzzle}")

        result = crypto_manager.verificar_rompecabezas_dispositivo(puzzle)
        print(f"Resultado de verificación: {result}")

    finally:
        # No eliminamos el dispositivo para evitar problemas con las relaciones
        # Solo cerramos la conexión
        db.close()

if __name__ == "__main__":
    test_crypto_functions()
