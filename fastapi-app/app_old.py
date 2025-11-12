"""
============================================================================
PLATAFORMA IoT - API FLASK
============================================================================
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import pymongo
import pymysql
import redis
import os
import logging
from datetime import datetime
from functools import wraps

# ============================================================================
# CONFIGURACIÓN DE APLICACIÓN
# ============================================================================

# Inicializar Flask
app = Flask(__name__)

# Configuración de CORS (permitir todos los orígenes temporalmente)
# TODO: Restringir a dominios específicos en producción
CORS(app)

# Configuración de secreto (para sesiones/JWT en futuro)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# ============================================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================================

# Obtener directorio de logs desde variable de entorno
LOGS_DIR = os.getenv('LOGS_DIR', '/app/logs')

# Crear directorio de logs si no existe
if not os.path.exists(LOGS_DIR):
    try:
        os.makedirs(LOGS_DIR)
    except Exception as e:
        print(f"Warning: Could not create logs directory {LOGS_DIR}: {e}")
        LOGS_DIR = '/tmp'

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler(f'{LOGS_DIR}/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info(f"Logging configurado. Directorio de logs: {LOGS_DIR}")

# ============================================================================
# CONFIGURACIÓN DE BASES DE DATOS
# ============================================================================

# Configuración MySQL
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'mysql'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'iot_user'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'iot_platform'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# Configuración MongoDB
MONGO_CONFIG = {
    'host': os.getenv('MONGO_HOST', 'mongodb'),
    'port': int(os.getenv('MONGO_PORT', 27017)),
    'username': os.getenv('MONGO_USER', 'admin'),
    'password': os.getenv('MONGO_PASSWORD', ''),
    'authSource': os.getenv('MONGO_AUTH_SOURCE', 'admin')
}

MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'iot_sensors')

# Configuración Redis
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'redis'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'password': os.getenv('REDIS_PASSWORD', ''),
    'decode_responses': True,
    'socket_connect_timeout': 5,
    'socket_timeout': 5
}

# ============================================================================
# FUNCIONES DE CONEXIÓN A BASES DE DATOS
# ============================================================================

def get_mysql_connection():
    """
    Crear y retornar conexión a MySQL
    
    Returns:
        pymysql.connections.Connection: Conexión a MySQL o None si falla
    """
    try:
        connection = pymysql.connect(**MYSQL_CONFIG)
        logger.debug("Conexión MySQL establecida exitosamente")
        return connection
    except Exception as e:
        logger.error(f"Error al conectar a MySQL: {str(e)}")
        return None


def get_mongo_client():
    """
    Crear y retornar cliente de MongoDB
    
    Returns:
        pymongo.MongoClient: Cliente MongoDB o None si falla
    """
    try:
        client = pymongo.MongoClient(**MONGO_CONFIG, serverSelectionTimeoutMS=5000)
        # Verificar conexión
        client.admin.command('ping')
        logger.debug("Conexión MongoDB establecida exitosamente")
        return client
    except Exception as e:
        logger.error(f"Error al conectar a MongoDB: {str(e)}")
        return None


def get_redis_client():
    """
    Crear y retornar cliente de Redis
    
    Returns:
        redis.Redis: Cliente Redis o None si falla
    """
    try:
        client = redis.Redis(**REDIS_CONFIG)
        # Verificar conexión
        client.ping()
        logger.debug("Conexión Redis establecida exitosamente")
        return client
    except Exception as e:
        logger.error(f"Error al conectar a Redis: {str(e)}")
        return None


# ============================================================================
# DECORADORES PERSONALIZADOS
# ============================================================================

def log_request(f):
    """
    Decorador para loggear todas las peticiones a endpoints
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# ENDPOINTS DE SALUD Y DIAGNÓSTICO
# ============================================================================

@app.route('/', methods=['GET'])
@log_request
def root():
    """
    Endpoint raíz - Información de la API
    
    Returns:
        JSON: Información básica de la API y endpoints disponibles
    """
    return jsonify({
        'name': 'IoT Platform API',
        'version': '1.0.0',
        'status': 'operational',
        'timestamp': datetime.utcnow().isoformat(),
        'endpoints': {
            'health': {
                'path': '/health',
                'method': 'GET',
                'description': 'Health check básico'
            },
            'detailed_health': {
                'path': '/health/detailed',
                'method': 'GET',
                'description': 'Health check detallado con estado de bases de datos'
            },
            'ping': {
                'path': '/api/ping',
                'method': 'GET',
                'description': 'Test de conectividad'
            },
            'info': {
                'path': '/api/info',
                'method': 'GET',
                'description': 'Información del sistema'
            }
        }
    }), 200


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check básico
    
    Returns:
        JSON: Estado de salud del servicio
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'IoT Platform API'
    }), 200


@app.route('/health/detailed', methods=['GET'])
@log_request
def detailed_health_check():
    """
    Health check detallado incluyendo conexiones a bases de datos
    
    Returns:
        JSON: Estado detallado de todos los servicios
        HTTP Status: 200 si todo OK, 503 si algún servicio falla
    """
    health_status = {
        'api': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'databases': {}
    }
    
    # Verificar MySQL
    try:
        mysql_conn = get_mysql_connection()
        if mysql_conn:
            with mysql_conn.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()
            mysql_conn.close()
            health_status['databases']['mysql'] = {
                'status': 'connected',
                'version': version['VERSION()'] if version else 'unknown'
            }
        else:
            health_status['databases']['mysql'] = {'status': 'error', 'message': 'Connection failed'}
    except Exception as e:
        health_status['databases']['mysql'] = {'status': 'error', 'message': str(e)}
    
    # Verificar MongoDB
    try:
        mongo_client = get_mongo_client()
        if mongo_client:
            server_info = mongo_client.server_info()
            mongo_client.close()
            health_status['databases']['mongodb'] = {
                'status': 'connected',
                'version': server_info.get('version', 'unknown')
            }
        else:
            health_status['databases']['mongodb'] = {'status': 'error', 'message': 'Connection failed'}
    except Exception as e:
        health_status['databases']['mongodb'] = {'status': 'error', 'message': str(e)}
    
    # Verificar Redis
    try:
        redis_client = get_redis_client()
        if redis_client:
            info = redis_client.info()
            health_status['databases']['redis'] = {
                'status': 'connected',
                'version': info.get('redis_version', 'unknown'),
                'used_memory': info.get('used_memory_human', 'unknown')
            }
        else:
            health_status['databases']['redis'] = {'status': 'error', 'message': 'Connection failed'}
    except Exception as e:
        health_status['databases']['redis'] = {'status': 'error', 'message': str(e)}
    
    # Determinar estado general
    all_healthy = all(
        db.get('status') == 'connected' 
        for db in health_status['databases'].values()
    )
    
    status_code = 200 if all_healthy else 503
    
    if not all_healthy:
        health_status['api'] = 'degraded'
    
    return jsonify(health_status), status_code


# ============================================================================
# ENDPOINTS DE API
# ============================================================================

@app.route('/api/ping', methods=['GET'])
@log_request
def ping():
    """
    Endpoint de ping para verificar conectividad desde internet
    
    Returns:
        JSON: Respuesta pong con información del cliente
    """
    logger.info(f"Ping recibido desde {request.remote_addr}")
    
    return jsonify({
        'message': 'pong',
        'timestamp': datetime.utcnow().isoformat(),
        'client_ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown'),
        'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }), 200


@app.route('/api/info', methods=['GET'])
@log_request
def system_info():
    """
    Información del sistema y configuración
    
    Returns:
        JSON: Información del sistema (sin datos sensibles)
    """
    return jsonify({
        'platform': 'IoT Backend Platform',
        'version': '1.0.0',
        'environment': os.getenv('FLASK_ENV', 'production'),
        'databases': {
            'mysql': {
                'host': MYSQL_CONFIG['host'],
                'database': MYSQL_CONFIG['database']
            },
            'mongodb': {
                'host': MONGO_CONFIG['host'],
                'database': MONGO_DATABASE
            },
            'redis': {
                'host': REDIS_CONFIG['host']
            }
        },
        'timestamp': datetime.utcnow().isoformat()
    }), 200


# ============================================================================
# MANEJO DE ERRORES
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Manejo de error 404 - Endpoint no encontrado"""
    logger.warning(f"404 Error: {request.path} from {request.remote_addr}")
    return jsonify({
        'error': 'Endpoint not found',
        'path': request.path,
        'timestamp': datetime.utcnow().isoformat()
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Manejo de error 500 - Error interno del servidor"""
    logger.error(f"500 Error: {str(error)} at {request.path}")
    return jsonify({
        'error': 'Internal server error',
        'timestamp': datetime.utcnow().isoformat()
    }), 500


@app.errorhandler(405)
def method_not_allowed(error):
    """Manejo de error 405 - Método no permitido"""
    logger.warning(f"405 Error: {request.method} {request.path} from {request.remote_addr}")
    return jsonify({
        'error': 'Method not allowed',
        'allowed_methods': error.valid_methods if hasattr(error, 'valid_methods') else [],
        'timestamp': datetime.utcnow().isoformat()
    }), 405


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == '__main__':
    logger.info("=" * 70)
    logger.info("INICIANDO PLATAFORMA IoT API")
    logger.info("=" * 70)
    logger.info(f"Ambiente: {os.getenv('FLASK_ENV', 'production')}")
    logger.info(f"Puerto: 5000")
    logger.info("=" * 70)
    
    # En producción, usar Gunicorn (ver Dockerfile CMD)
    # Este código solo se ejecuta en desarrollo
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False  # Siempre False en contenedor
    )
