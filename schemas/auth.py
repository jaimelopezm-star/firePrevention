from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class DeviceLogin(BaseModel):
    device_id: int
    api_key: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: Optional[int] = None
    device_id: Optional[int] = None
    admin_id: Optional[int] = None
    manager_id: Optional[int] = None
    role: Optional[str] = None
