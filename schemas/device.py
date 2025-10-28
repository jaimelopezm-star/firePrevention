from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DeviceBase(BaseModel):
    nombre: str
    device_type: str
    is_active: bool = True

class DeviceResponse(DeviceBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True