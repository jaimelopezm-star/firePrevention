"""
Configuración de MongoDB para almacenar datos de sensores IoT.

Este módulo gestiona la conexión a MongoDB y proporciona acceso
a las colecciones de datos de sensores (series temporales).
"""

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from typing import Optional
import logging
from core.config import settings

logger = logging.getLogger(__name__)

class MongoDBManager:
    """Gestor de conexión a MongoDB (Singleton)"""
    
    _client: Optional[MongoClient] = None
    _database: Optional[Database] = None
    
    @classmethod
    def get_client(cls) -> MongoClient:
        """
        Obtiene o crea el cliente de MongoDB.
        
        Returns:
            MongoClient: Cliente conectado a MongoDB
        """
        if cls._client is None:
            try:
                from urllib.parse import quote_plus
                
                # Codificar credenciales para caracteres especiales
                username = quote_plus(settings.MONGO_USER)
                password = quote_plus(settings.MONGO_PASSWORD)
                
                # Construir URI de conexión con autenticación
                mongo_uri = (
                    f"mongodb://{username}:{password}@"
                    f"{settings.MONGO_HOST}:{settings.MONGO_PORT}/"
                    f"{settings.MONGO_DATABASE}?authSource={settings.MONGO_AUTH_SOURCE}"
                )
                
                cls._client = MongoClient(
                    mongo_uri,
                    serverSelectionTimeoutMS=5000,  # Timeout de 5 segundos
                    connectTimeoutMS=5000,
                    socketTimeoutMS=5000
                )
                
                # Verificar conexión
                cls._client.admin.command('ping')
                logger.info(f"✅ Conexión a MongoDB establecida: {settings.MONGO_HOST}:{settings.MONGO_PORT}")
                
            except Exception as e:
                logger.error(f"❌ Error conectando a MongoDB: {e}")
                raise
        
        return cls._client
    
    @classmethod
    def get_database(cls) -> Database:
        """
        Obtiene la base de datos configurada.
        
        Returns:
            Database: Base de datos de MongoDB
        """
        if cls._database is None:
            client = cls.get_client()
            cls._database = client[settings.MONGO_DATABASE]
            logger.info(f"📂 Base de datos seleccionada: {settings.MONGO_DATABASE}")
        
        return cls._database
    
    @classmethod
    def get_collection(cls, collection_name: str) -> Collection:
        """
        Obtiene una colección específica.
        
        Args:
            collection_name: Nombre de la colección
            
        Returns:
            Collection: Colección de MongoDB
        """
        db = cls.get_database()
        return db[collection_name]
    
    @classmethod
    def close_connection(cls) -> None:
        """Cierra la conexión a MongoDB."""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._database = None
            logger.info("🔌 Conexión a MongoDB cerrada")


# Funciones de conveniencia para obtener colecciones específicas

def get_sensor_readings_collection() -> Collection:
    """
    Obtiene la colección de lecturas de sensores.
    
    Returns:
        Collection: Colección 'sensor_readings'
    """
    return MongoDBManager.get_collection("sensor_readings")


def get_device_logs_collection() -> Collection:
    """
    Obtiene la colección de logs de dispositivos.
    
    Returns:
        Collection: Colección 'device_logs'
    """
    return MongoDBManager.get_collection("device_logs")


def get_alerts_collection() -> Collection:
    """
    Obtiene la colección de alertas.
    
    Returns:
        Collection: Colección 'alerts'
    """
    return MongoDBManager.get_collection("alerts")


# Función para inicializar índices en las colecciones
def create_indexes():
    """
    Crea índices en las colecciones de MongoDB para optimizar consultas.
    
    Se ejecuta al iniciar la aplicación.
    """
    try:
        # Índices para sensor_readings
        sensor_readings = get_sensor_readings_collection()
        sensor_readings.create_index([("device_id", 1), ("timestamp", -1)])
        sensor_readings.create_index([("sensor_type", 1)])
        sensor_readings.create_index([("timestamp", -1)])
        
        # Índices para device_logs
        device_logs = get_device_logs_collection()
        device_logs.create_index([("device_id", 1), ("timestamp", -1)])
        
        # Índices para alerts
        alerts = get_alerts_collection()
        alerts.create_index([("device_id", 1), ("resolved", 1)])
        alerts.create_index([("timestamp", -1)])
        
        logger.info("✅ Índices de MongoDB creados correctamente")
        
    except Exception as e:
        logger.error(f"❌ Error creando índices en MongoDB: {e}")
