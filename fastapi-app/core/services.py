from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from core.validators import Validators
from models import User, Device, Admin, Manager
from datetime import timedelta



class AuthService:
    """Servicios reutilizables para autenticación"""

    @staticmethod
    def validate_user_credentials(db: Session, email: str, password: str, password_hashed: str) -> User:
        """Valida credenciales de usuario de forma segura"""
        user = db.query(User).filter(User.email == email).first()
        if not user or not getattr(user, "pasusuario", None):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        from core.security import verify_password
        if not verify_password(password, user.pasusuario.hashed_password):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        if not user.is_active:
            raise HTTPException(status_code=400, detail="Usuario desactivado")

        return user

    @staticmethod
    def validate_device_credentials(db: Session, device_id: int, api_key: str) -> Device:
        """Valida credenciales de dispositivo"""
        from models.pas_dispositivo import PasDispositivo
        
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device or not device.pasdispositivo_id:
            raise HTTPException(status_code=401, detail="Credenciales de dispositivo inválidas")
        
        # Obtener pasdispositivo para verificar api_key
        pas_disp = db.query(PasDispositivo).filter(PasDispositivo.id == device.pasdispositivo_id).first()
        if not pas_disp or pas_disp.api_key != api_key:
            raise HTTPException(status_code=401, detail="Credenciales de dispositivo inválidas")
        
        return device

    @staticmethod
    def authenticate_with_puzzle(obj, puzzle_response, db):
        """
        Autenticación modular por rompecabezas criptográfico para cualquier tipo de objeto (user, admin, manager, device).
        No verifica contraseña, solo la validez del puzzle.
        Args:
            obj: Instancia de User, Admin, Manager, Device, etc. (debe tener .id)
            puzzle_response: dict recibido del cliente
            db: sesión de base de datos
        Returns:
            True si autenticación exitosa, False si falla
        """
        from core.crypto_new import CryptoManager
        if not obj or not getattr(obj, "id", None):
            return False
        crypto_manager = CryptoManager(db)
        verification = crypto_manager.verificar_rompecabezas_dispositivo(puzzle_response)
        return verification.get('valido', False)

    @staticmethod
    def auth_by_password(entity, entity_type: str, email: str, password: str, db: Session):
        """
        Autenticación genérica por contraseña para cualquier entidad (User, Admin, Manager).
        Args:
            entity: Clase del modelo (User, Admin, Manager)
            entity_type: Tipo como string ("user", "admin", "manager")
            email: Email del usuario
            password: Contraseña en texto plano
            db: Sesión de base de datos
        Returns:
            dict con access_token, token_type, id, role
        """
        from core.security import verify_password, create_access_token
        
        # Buscar entidad por email
        obj = db.query(entity).filter(entity.email == email).first()
        
        # Determinar el campo de password según el tipo
        password_field_map = {
            "user": "pasusuario",
            "admin": "pasadmin",
            "manager": "pasgerente"
        }
        password_field = password_field_map.get(entity_type)
        
        if not obj or not getattr(obj, password_field, None):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        password_obj = getattr(obj, password_field)
        if not verify_password(password, password_obj.hashed_password):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        # Validar si está activo (solo User tiene is_active)
        if hasattr(obj, 'is_active') and not obj.is_active:
            raise HTTPException(status_code=400, detail="Usuario desactivado")
        
        # Generar token
        access_token_expires = timedelta(minutes=60)
        access_token = create_access_token(
            data={"sub": obj.email, "type": entity_type, "id": obj.id},
            expires_delta=access_token_expires
        )
        
        # Obtener rol (si existe)
        role_name = None
        if getattr(obj, "rol", None) and getattr(obj.rol, "name", None):
            role_name = obj.rol.name
        
        # Construir respuesta según tipo
        response = {
            "access_token": access_token,
            "token_type": "bearer",
            "role": role_name
        }
        
        # Agregar ID según el tipo
        if entity_type == "user":
            response["user_id"] = obj.id
        elif entity_type == "admin":
            response["admin_id"] = obj.id
        elif entity_type == "manager":
            response["manager_id"] = obj.id
        
        return response

    @staticmethod
    def auth_by_puzzle(entity, entity_type: str, email: str, puzzle_response: dict, db: Session):
        """
        Autenticación genérica por rompecabezas criptográfico para USUARIOS (NO usa contraseña).
        Args:
            entity: Clase del modelo (User, Admin, Manager)
            entity_type: Tipo como string ("user", "admin", "manager")
            email: Email del usuario
            puzzle_response: dict con la respuesta al rompecabezas
            db: Sesión de base de datos
        Returns:
            dict con access_token, token_type, id, role O dict con puzzle si no hay respuesta
        """
        from core.security import create_access_token
        from core.crypto_new import UserCryptoManager
        
        # Buscar entidad por email
        obj = db.query(entity).filter(entity.email == email).first()
        
        # Determinar el campo de password según el tipo (para validar que existe)
        password_field_map = {
            "user": "pasusuario",
            "admin": "pasadmin",
            "manager": "pasgerente"
        }
        password_field = password_field_map.get(entity_type)
        
        if not obj or not getattr(obj, password_field, None):
            raise HTTPException(status_code=401, detail="Entidad inválida")
        
        # Validar si está activo (solo User tiene is_active)
        if hasattr(obj, 'is_active') and not obj.is_active:
            raise HTTPException(status_code=400, detail="Usuario desactivado")
        
        # Manejar rompecabezas con UserCryptoManager
        crypto_manager = UserCryptoManager(db)
        
        if not puzzle_response:
            # Generar puzzle para usuario
            puzzle = crypto_manager.generar_rompecabezas_usuario(obj.id, entity_type, crypto_manager.server_id)
            response = {
                "access_token": "",
                "token_type": "bearer",
                "puzzle": puzzle
            }
            if entity_type == "user":
                response["user_id"] = obj.id
            elif entity_type == "admin":
                response["admin_id"] = obj.id
            elif entity_type == "manager":
                response["manager_id"] = obj.id
            return response
        
        # Verificar puzzle
        verification = crypto_manager.verificar_rompecabezas_usuario(puzzle_response, entity_type)
        if not verification.get('valido'):
            raise HTTPException(status_code=401, detail="Autenticación criptográfica fallida")
        
        # Generar token
        access_token_expires = timedelta(minutes=60)
        access_token = create_access_token(
            data={"sub": obj.email, "type": entity_type, "id": obj.id},
            expires_delta=access_token_expires
        )
        
        # Obtener rol (si existe)
        role_name = None
        if getattr(obj, "rol", None) and getattr(obj.rol, "name", None):
            role_name = obj.rol.name
        
        # Construir respuesta según tipo
        response = {
            "access_token": access_token,
            "token_type": "bearer",
            "role": role_name
        }
        
        # Agregar ID según el tipo
        if entity_type == "user":
            response["user_id"] = obj.id
        elif entity_type == "admin":
            response["admin_id"] = obj.id
        elif entity_type == "manager":
            response["manager_id"] = obj.id
        
        return response

    @staticmethod
    def auth_by_puzzle_device(device_id: int, api_key: str, puzzle_response: dict, db: Session):
        """
        Autenticación por rompecabezas criptográfico para DISPOSITIVOS.
        
        Flujo basado en la lógica original:
        1. El DISPOSITIVO genera el rompecabezas (calcula HMAC, cifra con su clave)
        2. El DISPOSITIVO envía el puzzle al servidor en puzzle_response
        3. El SERVIDOR verifica el puzzle (reconstruye HMAC, descifra, compara)
        
        Args:
            device_id (int): ID del dispositivo
            api_key (str): API key del dispositivo
            puzzle_response: dict con el rompecabezas generado por el dispositivo.
                            Debe contener: 'id_origen', 'Random dispositivo', 'Parametro de identidad cifrado'
            db: Sesión de base de datos
        Returns:
            dict con access_token, token_type, device_id
        """
        from core.security import create_access_token
        from core.crypto_new import CryptoManager
        
        # Validar dispositivo por ID y API key
        from models.pas_dispositivo import PasDispositivo
        
        db_device = db.query(Device).filter(Device.id == device_id).first()
        if not db_device or not db_device.pasdispositivo_id:
            raise HTTPException(status_code=401, detail="Credenciales de dispositivo inválidas")
        
        # Obtener pasdispositivo para verificar api_key
        pas_disp = db.query(PasDispositivo).filter(PasDispositivo.id == db_device.pasdispositivo_id).first()
        if not pas_disp or pas_disp.api_key != api_key:
            raise HTTPException(status_code=401, detail="Credenciales de dispositivo inválidas")
        
        # El dispositivo DEBE enviar el puzzle que generó
        if not puzzle_response:
            raise HTTPException(
                status_code=400, 
                detail="Se requiere puzzle_response. El dispositivo debe generar y enviar el rompecabezas criptográfico."
            )
        
        # Verificar puzzle generado por el dispositivo
        crypto_manager = CryptoManager(db)
        verification = crypto_manager.verificar_rompecabezas_dispositivo(puzzle_response)
        
        if not verification.get('valido'):
            error_msg = verification.get('error', 'Autenticación criptográfica fallida')
            raise HTTPException(status_code=401, detail=error_msg)
        
        # Generar token JWT
        access_token_expires = timedelta(minutes=1440)  # 24 horas para dispositivos
        access_token = create_access_token(
            data={"sub": str(db_device.id), "type": "device"},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "device_id": db_device.id
        }


class UserService:
    """Servicios para gestión de usuarios"""

    @staticmethod
    def validate_new_user(db: Session, email: str, password: str):
        """Valida datos para nuevo usuario"""
        if not Validators.validate_email(email):
            raise HTTPException(status_code=400, detail="Formato de email inválido")

        if not Validators.validate_password_strength(password):
            raise HTTPException(
                status_code=400,
                detail="La contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula y un número"
            )

        if db.query(User).filter(User.email == email).first():
            raise HTTPException(status_code=400, detail="Email ya registrado")