"""
Schemas Pydantic para validación de datos de sensores.

Define las estructuras de datos para:
- Lecturas de sensores (entrada/salida)
- Respuestas del servidor
- Consultas históricas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class SensorReading(BaseModel):
    """
    Schema para recibir lecturas de sensores desde dispositivos IoT.
    
    El dispositivo envía múltiples lecturas de sensores en un solo request.
    El servidor normalizará esto a documentos individuales en MongoDB.
    """
    device_id: int = Field(..., description="ID del dispositivo que envía las lecturas")
    temperature: Optional[float] = Field(None, description="Temperatura en grados Celsius")
    smoke_level: Optional[int] = Field(None, ge=0, le=100, description="Nivel de humo (0-100%)")
    battery: Optional[int] = Field(None, ge=0, le=100, description="Nivel de batería (0-100%)")
    location: Optional[str] = Field(None, max_length=200, description="Ubicación del dispositivo")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Timestamp del evento")
    
    @validator('temperature')
    def validate_temperature(cls, v):
        if v is not None and (v < -50 or v > 100):
            raise ValueError('Temperatura fuera de rango válido (-50 a 100°C)')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "device_id": 5,
                "temperature": 25.3,
                "smoke_level": 5,
                "battery": 85,
                "location": "Sala Principal",
                "timestamp": "2025-11-30T10:30:00Z"
            }
        }


class SensorReadingResponse(BaseModel):
    """Response después de insertar lecturas en MongoDB."""
    message: str
    readings_count: int
    device_id: int
    inserted_ids: List[str]
    timestamp: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Lecturas recibidas y guardadas exitosamente",
                "readings_count": 3,
                "device_id": 5,
                "inserted_ids": [
                    "673f5e2a1234567890abcdef",
                    "673f5e2a1234567890abcdeg",
                    "673f5e2a1234567890abcdeh"
                ],
                "timestamp": "2025-11-30T10:30:00Z"
            }
        }


class SensorDocument(BaseModel):
    """
    Schema de un documento individual en MongoDB.
    
    Cada lectura se normaliza a un documento separado por tipo de sensor.
    """
    device_id: int  # Mantener como integer (coincide con MySQL)
    sensor_type: str  # "temperature", "smoke_level", "battery"
    value: float
    unit: str  # "°C", "%", etc.
    location: Optional[str] = None
    timestamp: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "5",
                "sensor_type": "temperature",
                "value": 25.3,
                "unit": "°C",
                "location": "Sala Principal",
                "timestamp": "2025-11-30T10:30:00Z"
            }
        }


class SensorReadingHistory(BaseModel):
    """Schema para consultas históricas de lecturas."""
    device_id: int
    sensor_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, le=1000, description="Máximo de registros a retornar")
    
    class Config:
        json_schema_extra = {
            "example": {
                "device_id": 5,
                "sensor_type": "temperature",
                "start_date": "2025-11-01T00:00:00Z",
                "end_date": "2025-11-30T23:59:59Z",
                "limit": 100
            }
        }


class SensorReadingItem(BaseModel):
    """Item individual en respuesta de histórico."""
    sensor_type: str
    value: float
    unit: str
    location: Optional[str]
    timestamp: datetime


class SensorReadingsHistoryResponse(BaseModel):
    """Response para consultas históricas."""
    device_id: int
    readings_count: int
    readings: List[SensorReadingItem]
    
    class Config:
        json_schema_extra = {
            "example": {
                "device_id": 5,
                "readings_count": 150,
                "readings": [
                    {
                        "sensor_type": "temperature",
                        "value": 25.3,
                        "unit": "°C",
                        "location": "Sala Principal",
                        "timestamp": "2025-11-30T10:30:00Z"
                    },
                    {
                        "sensor_type": "smoke_level",
                        "value": 5,
                        "unit": "%",
                        "location": "Sala Principal",
                        "timestamp": "2025-11-30T10:30:00Z"
                    }
                ]
            }
        }
