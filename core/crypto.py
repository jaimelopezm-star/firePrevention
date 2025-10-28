import os
from base64 import b64decode, b64encode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import hashlib
import hmac
from sqlalchemy.orm import Session
from models.device import Device
from models.pas_dispositivo import PasDispositivo

class CryptoManager:
    def __init__(self, db: Session):
        self.db = db
        self.server_key = os.urandom(32)  # Considera almacenar esto en un lugar seguro
        self.server_id = 'server_main_001'

    def register_device_key(self, device_id: int, key: bytes = None) -> bytes:
        try:
            if key is None:
                key = os.urandom(32)
            
            device = self.db.query(Device).filter(Device.id == device_id).first()
            if not device:
                raise ValueError(f"No se encontró el dispositivo con ID: {device_id}")
                
            if not device.pasdispositivo:
                # Crear nuevo PasDispositivo con encryption_key
                pas_dispositivo = PasDispositivo(encryption_key=key)
                device.pasdispositivo = pas_dispositivo
            else:
                # Actualizar encryption_key existente
                device.pasdispositivo.encryption_key = key
                
            self.db.commit()
            return key
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Error al registrar la clave: {str(e)}")

    def get_key_by_id(self, device_id: int) -> bytes:
        device = self.db.query(Device).filter(Device.id == device_id).first()
        if not device or not device.pasdispositivo:
            return None
        return device.pasdispositivo.encryption_key

    def cifrar_aes256(self, data: bytes, key: bytes) -> dict:
        iv = os.urandom(16)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        data_padded = pad(data, AES.block_size)
        ciphertext = cipher.encrypt(data_padded)

        return {
            'ciphertext': b64encode(ciphertext).decode('utf-8'),
            'iv': b64encode(iv).decode('utf-8')
        }

    def descifrar_aes256(self, encrypted_data: dict, key: bytes) -> bytes:
        ciphertext = b64decode(encrypted_data['ciphertext'])
        iv = b64decode(encrypted_data['iv'])

        cipher = AES.new(key, AES.MODE_CBC, iv)
        data_padded = cipher.decrypt(ciphertext)
        data = unpad(data_padded, AES.block_size)

        return data

    def generar_rompecabezas_dispositivo(self, id_dispositivo: int, id_servidor: str) -> dict:
        r2 = os.urandom(32)  # generar numero random del dispositivo
        
        key_b = self.get_key_by_id(id_dispositivo)  # key del dispositivo
        key_a = self.server_key  # key del servidor

        if key_b is None:
            raise ValueError(f"No se encontró key del dispositivo: {id_dispositivo}")

        hmac_key = key_b + key_a  # hasheo con llaves
        p2 = hmac.new(hmac_key, r2, hashlib.sha256).digest()
        p2c = self.cifrar_aes256(p2, key_b)  # cifrar P2 con key del dispositivo

        return {
            'id_origen': id_dispositivo,
            'id_destino': id_servidor,
            'R2': b64encode(r2).decode('utf-8'),
            'P2c': p2c,
        }

    def verificar_rompecabezas_dispositivo(self, rc_dispositivo_json: dict) -> dict:
        id_origen = rc_dispositivo_json['id_origen']
        id_destino = rc_dispositivo_json['id_destino']
        r2 = b64decode(rc_dispositivo_json['R2'])
        p2c = rc_dispositivo_json['P2c']

        key_b = self.get_key_by_id(id_origen)  # key del dispositivo
        key_a = self.server_key  # key del servidor

        if key_b is None:
            return {'valido': False, 'error': 'Key del dispositivo no encontrada'}

        hmac_key = key_b + key_a  # reconstruir P2
        p2_reconstruida = hmac.new(hmac_key, r2, hashlib.sha256).digest()

        try:
            p2_descifrada = self.descifrar_aes256(p2c, key_b)  # descifrar con la key del dispositivo
        except Exception as e:
            return {'valido': False, 'error': f'Error al descifrar: {e}'}

        if p2_reconstruida == p2_descifrada:  # comparar ambas P2
            return {
                'valido': True,
                'mensaje': 'Dispositivo autenticado correctamente',
                'id_origen': id_origen,
                'id_destino': id_destino
            }
        else:
            return {'valido': False, 'error': 'P2 no coincide - Dispositivo NO autenticado'}
