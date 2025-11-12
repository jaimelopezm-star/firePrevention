from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    # Ya no se usa rompecabezas para usuarios/admin/manager


class DeviceLogin(BaseModel):
    device_id: int
    api_key: str
    # El dispositivo GENERA y envía el rompecabezas criptográfico para autenticarse
    # Debe contener: 'id_origen', 'Random dispositivo' (base64), 'Parametro de identidad cifrado' (dict con ciphertext e iv)
    puzzle_response: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "device_id": 5,
                "api_key": "CFr9woIVKTSQ3YPnwUcYvKOc1FqKx8bi",
                "puzzle_response": {
                    "id_origen": 5,
                    "Random dispositivo": "base64_encoded_32_bytes...",
                    "Parametro de identidad cifrado": {
                        "ciphertext": "base64_encoded_ciphertext...",
                        "iv": "base64_encoded_iv..."
                    }
                }
            }
        }


class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: Optional[int] = None
    device_id: Optional[int] = None
    admin_id: Optional[int] = None
    manager_id: Optional[int] = None
    role: Optional[str] = None
    # Si el endpoint devuelve un rompecabezas (antes de emitir token), se puede incluir aquí
    puzzle: Optional[Dict[str, Any]] = None
