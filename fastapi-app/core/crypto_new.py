import os
from base64 import b64decode, b64encode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import hashlib
import hmac
from sqlalchemy.orm import Session
from models.device import Device
from models.pas_dispositivo import PasDispositivo
from core.config import settings


class CryptoManager:
    """
    Gestor criptográfico para manejar claves de dispositivos, cifrado AES-256,
    y un mecanismo de autenticación basado en 'rompecabezas criptográficos'.
    """

    def __init__(self, db: Session):
        """
        Inicializa el gestor con una sesión de base de datos.
        Importante: la clave secreta del servidor (server_key) debe ser
        DETERMINÍSTICA entre procesos/instancias para evitar fallos cuando
        hay múltiples workers de Uvicorn/Gunicorn o reinicios del contenedor.

        Por eso la derivamos de settings.SECRET_KEY usando SHA-256, en lugar
        de generarla aleatoria en memoria.
        """
        self.db = db
        # Deriva una clave binaria de 32 bytes (AES-256/HMAC) estable entre workers
        # Usamos un contexto fijo para no interferir con otros usos del SECRET_KEY
        self.server_key = hashlib.sha256((settings.SECRET_KEY + "|puzzle_v1").encode("utf-8")).digest()
        # Un identificador estable del servidor (opcional). Si existe HOSTNAME en Docker, úsalo.
        self.server_id = os.getenv('HOSTNAME', 'server_main_001')

    def register_device_key(self, device_id: int, key: bytes = None) -> bytes:
        """
        Registra o actualiza la clave de cifrado de un dispositivo en la base de datos.
        
        Args:
            device_id (int): ID del dispositivo.
            key (bytes, opcional): Clave personalizada. Si no se proporciona, se genera una aleatoria.
        
        Returns:
            bytes: La clave registrada (ya sea nueva o proporcionada).
        """
        try:
            if key is None:
                key = os.urandom(32)  # Genera una clave AES-256 aleatoria

            # Busca el dispositivo en la base de datos
            device = self.db.query(Device).filter(Device.id == device_id).first()
            if not device:
                raise ValueError(f"No se encontró el dispositivo con ID: {device_id}")

            # Buscar o crear PasDispositivo usando el pasdispositivo_id
            if device.pasdispositivo_id:
                pas_dispositivo = self.db.query(PasDispositivo).filter(
                    PasDispositivo.id == device.pasdispositivo_id
                ).first()
                if pas_dispositivo:
                    # Actualizar clave existente
                    pas_dispositivo.encryption_key = key
                else:
                    raise ValueError(f"pasdispositivo con ID {device.pasdispositivo_id} no encontrado")
            else:
                # Crear nuevo PasDispositivo si no existe
                pas_dispositivo = PasDispositivo(encryption_key=key)
                self.db.add(pas_dispositivo)
                self.db.flush()  # Para obtener el ID
                device.pasdispositivo_id = pas_dispositivo.id

            self.db.commit()
            return key
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Error al registrar la clave: {str(e)}")

    def get_key_by_id(self, device_id: int) -> bytes:
        """
        Recupera la clave de cifrado de un dispositivo desde la base de datos.
        
        Args:
            device_id (int): ID del dispositivo.
        
        Returns:
            bytes | None: Clave del dispositivo o None si no existe.
        """
        device = self.db.query(Device).filter(Device.id == device_id).first()
        if not device or not device.pasdispositivo_id:
            return None
        
        # Buscar el PasDispositivo por ID
        pas_dispositivo = self.db.query(PasDispositivo).filter(
            PasDispositivo.id == device.pasdispositivo_id
        ).first()
        
        if not pas_dispositivo:
            return None
        
        return pas_dispositivo.encryption_key

    def cifrar_aes256(self, data: bytes, key: bytes) -> dict:
        """
        Cifra datos usando AES-256 en modo CBC.
        
        Args:
            data (bytes): Datos a cifrar.
            key (bytes): Clave de 32 bytes para AES-256.
        
        Returns:
            dict: Contiene 'ciphertext' e 'iv' codificados en base64 (JSON serializable).
        """
        iv = os.urandom(16)  # Vector de inicialización aleatorio (16 bytes)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        data_padded = pad(data, AES.block_size)  # Aplica padding PKCS7
        ciphertext = cipher.encrypt(data_padded)
        return {
            'ciphertext': b64encode(ciphertext).decode('utf-8'),
            'iv': b64encode(iv).decode('utf-8')
        }

    def descifrar_aes256(self, encrypted_data: dict, key: bytes) -> bytes:
        """
        Descifra datos cifrados con AES-256 en modo CBC.
        
        Args:
            encrypted_data (dict): Debe contener 'ciphertext' e 'iv' en base64.
            key (bytes): Clave de 32 bytes usada para cifrar.
        
        Returns:
            bytes: Datos originales descifrados y sin padding.
        """
        ciphertext = b64decode(encrypted_data['ciphertext'])
        iv = b64decode(encrypted_data['iv'])
        cipher = AES.new(key, AES.MODE_CBC, iv)
        data_padded = cipher.decrypt(ciphertext)
        return unpad(data_padded, AES.block_size)  # Elimina el padding

    def generar_rompecabezas_dispositivo(self, id_dispositivo: int, id_servidor: str) -> dict:
        """
        Genera un 'rompecabezas criptográfico' para autenticar un dispositivo.
        Este rompecabezas incluye un valor aleatorio (R2) y un HMAC cifrado (P2c).
        
        Flujo:
        - El servidor genera R2 (32 bytes aleatorios).
        - Calcula P2 = HMAC-SHA256(key_b + server_key, R2)
        - Cifra P2 con la clave del dispositivo (key_b) → P2c
        - Envía R2 y P2c al dispositivo para que lo resuelva.
        
        Args:
            id_dispositivo (int): ID del dispositivo a autenticar.
            id_servidor (str): ID del servidor (normalmente self.server_id).
        
        Returns:
            dict: Rompecabezas listo para enviar al dispositivo.
        """
        r2 = os.urandom(32)  # Valor aleatorio desafío
        key_b = self.get_key_by_id(id_dispositivo)
        if key_b is None:
            raise ValueError(f"No se encontró key del dispositivo: {id_dispositivo}")

        # Deriva una clave HMAC combinando la clave del dispositivo y la del servidor
        hmac_key = key_b + self.server_key
        p2 = hmac.new(hmac_key, r2, hashlib.sha256).digest()  # P2 = HMAC(R2)

        # Cifra P2 con la clave del dispositivo → P2c
        p2c = self.cifrar_aes256(p2, key_b)

        return {
            'id_origen': id_dispositivo,
            'id_destino': id_servidor,
            'R2': b64encode(r2).decode('utf-8'),  # R2 en claro (pero aleatorio)
            'P2c': p2c,  # P2 cifrado
        }

    def verificar_rompecabezas_dispositivo(self, rc_dispositivo_json: dict) -> dict:
        """
        Verifica un rompecabezas generado por el DISPOSITIVO.
        
        Flujo original (correcto):
        1. El dispositivo genera R2 (random) 
        2. El dispositivo calcula P2 = HMAC(key_dispositivo + key_servidor, R2)
        3. El dispositivo cifra P2 con su clave → P2c
        4. El dispositivo envía {'id_origen', 'Random dispositivo', 'Parametro de identidad cifrado'}
        5. El servidor reconstruye P2, descifra P2c recibido y compara
        
        Args:
            rc_dispositivo_json (dict): Rompecabezas generado por el dispositivo.
                Acepta dos formatos:
                - Original: 'id_origen', 'Random dispositivo', 'Parametro de identidad cifrado'
                - Alternativo: 'id_origen', 'R2', 'P2c' (para compatibilidad)
        
        Returns:
            dict: {'valido': bool, 'mensaje'/'error': str, 'id_origen': int, 'id_destino': str}
        """
        try:
            id_origen = rc_dispositivo_json['id_origen']
            
            # Soportar ambas nomenclaturas (original y alternativa)
            if 'Random dispositivo' in rc_dispositivo_json:
                ran_dev = b64decode(rc_dispositivo_json['Random dispositivo'])
                parametro_id_cif = rc_dispositivo_json['Parametro de identidad cifrado']
            else:
                ran_dev = b64decode(rc_dispositivo_json['R2'])
                parametro_id_cif = rc_dispositivo_json['P2c']

            # Obtiene la clave del dispositivo
            key_b = self.get_key_by_id(id_origen)
            if key_b is None:
                return {'valido': False, 'error': 'Key del dispositivo no encontrada'}

            # Reconstruye el parámetro de identidad usando R2 y la clave derivada
            hmac_key = key_b + self.server_key
            parametro_id_reconstruida = hmac.new(hmac_key, ran_dev, hashlib.sha256).digest()

            # Descifra el parámetro de identidad recibido
            try:
                parametro_id_descif = self.descifrar_aes256(parametro_id_cif, key_b)
            except Exception as e:
                return {'valido': False, 'error': f'Error al descifrar: {e}'}

            # Compara los valores
            if parametro_id_reconstruida == parametro_id_descif:
                return {
                    'valido': True,
                    'mensaje': 'Dispositivo autenticado correctamente',
                    'id_origen': id_origen,
                    'id_destino': self.server_id
                }
            else:
                return {'valido': False, 'error': 'Parámetro de identidad no coincide - Dispositivo NO autenticado'}
        
        except KeyError as e:
            return {'valido': False, 'error': f'Campo faltante en puzzle: {e}'}
        except Exception as e:
            return {'valido': False, 'error': f'Error en verificación: {e}'}


class UserCryptoManager(CryptoManager):
    """
    Gestor criptográfico especializado para USUARIOS (User, Admin, Manager).
    Extiende CryptoManager pero busca encryption_key en pasusuario/pasadmin/pasgerente
    en lugar de pasdispositivo.
    """

    def get_key_by_user_id(self, user_id: int, user_type: str = "user") -> bytes:
        """
        Recupera la clave de cifrado de un usuario desde la base de datos.
        
        Args:
            user_id (int): ID del usuario/admin/manager.
            user_type (str): Tipo de usuario ("user", "admin", "manager")
        
        Returns:
            bytes | None: Clave del usuario o None si no existe.
        """
        from models import User, Admin, Manager
        
        model_map = {
            "user": (User, "pasusuario"),
            "admin": (Admin, "pasadmin"),
            "manager": (Manager, "pasgerente")
        }
        
        if user_type not in model_map:
            return None
        
        model, password_field = model_map[user_type]
        user_obj = self.db.query(model).filter(model.id == user_id).first()
        
        if not user_obj or not getattr(user_obj, password_field, None):
            return None
        
        pas_obj = getattr(user_obj, password_field)
        return pas_obj.encryption_key if hasattr(pas_obj, 'encryption_key') else None

    def register_user_key(self, user_id: int, user_type: str = "user", key: bytes = None) -> bytes:
        """
        Registra o actualiza la clave de cifrado de un usuario en la base de datos.
        
        Args:
            user_id (int): ID del usuario/admin/manager.
            user_type (str): Tipo de usuario ("user", "admin", "manager")
            key (bytes, opcional): Clave personalizada. Si no se proporciona, se genera una aleatoria.
        
        Returns:
            bytes: La clave registrada (ya sea nueva o proporcionada).
        """
        from models import User, Admin, Manager
        
        try:
            if key is None:
                key = os.urandom(32)  # Genera una clave AES-256 aleatoria

            model_map = {
                "user": (User, "pasusuario"),
                "admin": (Admin, "pasadmin"),
                "manager": (Manager, "pasgerente")
            }
            
            if user_type not in model_map:
                raise ValueError(f"Tipo de usuario inválido: {user_type}")
            
            model, password_field = model_map[user_type]
            user_obj = self.db.query(model).filter(model.id == user_id).first()
            
            if not user_obj:
                raise ValueError(f"No se encontró el {user_type} con ID: {user_id}")

            pas_obj = getattr(user_obj, password_field)
            if not pas_obj:
                raise ValueError(f"No se encontró el registro de password para {user_type} ID: {user_id}")
            
            pas_obj.encryption_key = key
            self.db.commit()
            return key
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Error al registrar la clave: {str(e)}")

    def generar_rompecabezas_usuario(self, user_id: int, user_type: str, id_servidor: str) -> dict:
        """
        Genera un 'rompecabezas criptográfico' para autenticar un usuario.
        Similar a generar_rompecabezas_dispositivo pero busca la clave en pasusuario/pasadmin/pasgerente.
        
        Args:
            user_id (int): ID del usuario/admin/manager a autenticar.
            user_type (str): Tipo ("user", "admin", "manager")
            id_servidor (str): ID del servidor (normalmente self.server_id).
        
        Returns:
            dict: Rompecabezas listo para enviar al cliente.
        """
        r2 = os.urandom(32)  # Valor aleatorio desafío
        key_b = self.get_key_by_user_id(user_id, user_type)
        
        if key_b is None:
            # Si no tiene clave, generar una automáticamente
            key_b = self.register_user_key(user_id, user_type)

        # Deriva una clave HMAC combinando la clave del usuario y la del servidor
        hmac_key = key_b + self.server_key
        p2 = hmac.new(hmac_key, r2, hashlib.sha256).digest()  # P2 = HMAC(R2)

        # Cifra P2 con la clave del usuario → P2c
        p2c = self.cifrar_aes256(p2, key_b)

        return {
            'id_origen': user_id,
            'id_destino': id_servidor,
            'R2': b64encode(r2).decode('utf-8'),
            'P2c': p2c,
        }

    def verificar_rompecabezas_usuario(self, rc_usuario_json: dict, user_type: str) -> dict:
        """
        Verifica la respuesta de un usuario al rompecabezas.
        
        Args:
            rc_usuario_json (dict): Debe contener 'id_origen', 'id_destino', 'R2' (b64), 'P2c'.
            user_type (str): Tipo de usuario ("user", "admin", "manager")
        
        Returns:
            dict: Resultado de la verificación con estado y mensaje.
        """
        id_origen = rc_usuario_json['id_origen']
        id_destino = rc_usuario_json['id_destino']
        r2 = b64decode(rc_usuario_json['R2'])
        p2c = rc_usuario_json['P2c']

        # Obtiene la clave del usuario
        key_b = self.get_key_by_user_id(id_origen, user_type)
        if key_b is None:
            return {'valido': False, 'error': f'Key del {user_type} no encontrada'}

        # Reconstruye P2 usando R2 y la clave derivada
        hmac_key = key_b + self.server_key
        p2_reconstruida = hmac.new(hmac_key, r2, hashlib.sha256).digest()

        # Descifra P2c recibido
        try:
            p2_descifrada = self.descifrar_aes256(p2c, key_b)
        except Exception as e:
            return {'valido': False, 'error': f'Error al descifrar: {e}'}

        # Compara los valores
        if p2_reconstruida == p2_descifrada:
            return {
                'valido': True,
                'mensaje': f'{user_type.capitalize()} autenticado correctamente',
                'id_origen': id_origen,
                'id_destino': id_destino
            }
        else:
            return {'valido': False, 'error': f'P2 no coincide - {user_type.capitalize()} NO autenticado'}