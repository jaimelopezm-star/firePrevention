from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    nombre: str
    email: EmailStr
    is_active: bool = True

class UserCreate(UserBase):
    password: str
    rol_id: int

class UserResponse(UserBase):
    id: int
    rol: str
    created_at: datetime

    class Config:
        from_attributes = True


# ========== SCHEMAS PARA MANAGERS ==========

class ManagerBase(BaseModel):
    nombre: str
    email: EmailStr

class ManagerCreate(ManagerBase):
    password: str
    admin_id: int

class ManagerResponse(ManagerBase):
    id: int
    admin_id: int
    created_at: datetime

    class Config:
        from_attributes = True
