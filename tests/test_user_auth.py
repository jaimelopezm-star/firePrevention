from database import SessionLocal
from core.crypto import CryptoManager
from models.user import User
from models.pas_usuario import PasUsuario
from core.security import get_password_hash
import json
import requests
import bcrypt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def test_user_auth_with_puzzle():
    # Crear una sesión de base de datos
    db = SessionLocal()
    test_user = None
    pas_usuario = None
    
    try:
        # Verificar si el usuario de prueba ya existe
        existing_user = db.query(User).filter(User.email == "test@example.com").first()
        if existing_user:
            pas_id = existing_user.pasusuario_id
            db.delete(existing_user)
            db.commit()
            if pas_id:
                db.query(PasUsuario).filter(PasUsuario.id == pas_id).delete()
                db.commit()

        # 1. Crear las credenciales primero
        test_password = "test123"  # Contraseña más corta
        from core.security import get_password_hash
        hashed_password = get_password_hash(test_password[:72])  # Asegurar que no exceda el límite de bcrypt
        pas_usuario = PasUsuario(
            hashed_password=hashed_password
        )
        db.add(pas_usuario)
        db.commit()
        db.refresh(pas_usuario)

        # 2. Crear el usuario y vincularlo con las credenciales
        test_user = User(
            nombre="Usuario Prueba",
            email="test@example.com",
            is_active=True,
            rol_id=1,  # Asumiendo que tienes el rol 1 en tu base de datos
            pasusuario_id=pas_usuario.id  # Esta es la clave: vincular con el pasusuario
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        print(f"\nUsuario de prueba creado:")
        print(f"ID: {test_user.id}")
        print(f"Email: {test_user.email}")
        print(f"Password (sin hash): {test_password}")

        # 3. Primer paso: solicitar el rompecabezas
        login_data = {
            "email": test_user.email,
            "password": test_password
        }

        # Hacer la primera solicitud para obtener el puzzle
        response = requests.post(
            "http://localhost:8001/api/v1/auth/login/user",
            json=login_data
        )
        
        if response.status_code != 200:
            print(f"Error en la primera solicitud: {response.status_code}")
            print(response.json())
            return

        first_response = response.json()
        puzzle = first_response.get("puzzle")
        
        print("\nRompecabezas recibido:")
        print(json.dumps(puzzle, indent=2))

        # 4. Segundo paso: enviar el puzzle resuelto
        login_data["puzzle_response"] = puzzle
        
        # Hacer la segunda solicitud con el puzzle
        response = requests.post(
            "http://localhost:8001/api/v1/auth/login/user",
            json=login_data
        )

        print("\nRespuesta final:")
        print(json.dumps(response.json(), indent=2))

    except Exception as e:
        print(f"Error durante la prueba: {str(e)}")
    finally:
        try:
            # Limpiar datos de prueba
            if test_user and test_user.id:
                # Obtener el pasusuario_id antes de eliminar el usuario
                pas_id = test_user.pasusuario_id
                # Primero eliminar el usuario
                db.query(User).filter(User.id == test_user.id).delete()
                db.commit()
                # Luego eliminar PasUsuario si existe
                if pas_id:
                    db.query(PasUsuario).filter(PasUsuario.id == pas_id).delete()
                    db.commit()
        except Exception as e:
            print(f"Error durante la limpieza: {str(e)}")
        finally:
            db.close()

if __name__ == "__main__":
    test_user_auth_with_puzzle()