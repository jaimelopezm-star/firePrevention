-- ============================================================================
-- Script de Inicialización MySQL - Plataforma IoT
-- ============================================================================

-- Usar base de datos
USE iot_platform;

-- ============================================================================
-- TABLA: users
-- Descripción: Usuarios del sistema (administradores, operadores)
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'operator', 'viewer') DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- TABLA: devices
-- Descripción: Dispositivos IoT registrados
-- ============================================================================
CREATE TABLE IF NOT EXISTS devices (
    device_id VARCHAR(50) PRIMARY KEY,
    device_name VARCHAR(100) NOT NULL,
    device_type ENUM('sensor', 'actuator', 'gateway') NOT NULL,
    api_key_hash VARCHAR(255) NOT NULL,
    owner_id INT,
    location VARCHAR(255),
    status ENUM('active', 'inactive', 'maintenance', 'error') DEFAULT 'active',
    firmware_version VARCHAR(20),
    last_seen TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_status (status),
    INDEX idx_device_type (device_type),
    INDEX idx_owner (owner_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- TABLA: sensors
-- Descripción: Sensores específicos asociados a dispositivos
-- ============================================================================
CREATE TABLE IF NOT EXISTS sensors (
    sensor_id VARCHAR(50) PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL,
    sensor_type ENUM('temperature', 'humidity', 'co2', 'water_valve', 'light', 'motion') NOT NULL,
    sensor_name VARCHAR(100),
    unit VARCHAR(20),
    min_value DECIMAL(10,2),
    max_value DECIMAL(10,2),
    calibration_offset DECIMAL(10,4) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE,
    INDEX idx_device (device_id),
    INDEX idx_type (sensor_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- TABLA: api_keys
-- Descripción: Claves API para autenticación de dispositivos
-- ============================================================================
CREATE TABLE IF NOT EXISTS api_keys (
    key_id INT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    key_name VARCHAR(100),
    permissions JSON,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP NULL,
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE,
    INDEX idx_device (device_id),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- DATOS DE PRUEBA (Comentar en producción)
-- ============================================================================

-- Usuario de prueba (password: Test123!)
-- NOTA: Cambiar en producción con hash real de bcrypt
INSERT INTO users (username, email, password_hash, role) VALUES
('admin', 'admin@iotplatform.local', '$2b$12$ejemplo_hash_bcrypt', 'admin'),
('viewer', 'viewer@iotplatform.local', '$2b$12$ejemplo_hash_bcrypt', 'viewer');

-- Dispositivo de prueba
INSERT INTO devices (device_id, device_name, device_type, api_key_hash, owner_id, location) VALUES
('DEV001', 'Sensor Greenhouse 1', 'sensor', '$2b$12$ejemplo_hash_api_key', 1, 'Invernadero Principal');

-- Sensores de prueba
INSERT INTO sensors (sensor_id, device_id, sensor_type, sensor_name, unit, min_value, max_value) VALUES
('SENS_TEMP_001', 'DEV001', 'temperature', 'Temperatura Ambiente', '°C', -10.00, 50.00),
('SENS_HUM_001', 'DEV001', 'humidity', 'Humedad Relativa', '%', 0.00, 100.00),
('SENS_CO2_001', 'DEV001', 'co2', 'CO2 Ambiente', 'ppm', 0.00, 5000.00);

-- ============================================================================
-- FIN DEL SCRIPT
-- ============================================================================
