// ============================================================================
// Script de Inicialización MongoDB - Plataforma IoT
// ============================================================================

// Conectar a la base de datos
db = db.getSiblingDB('iot_sensors');

// ============================================================================
// COLECCIÓN: sensor_readings
// Descripción: Lecturas de sensores (time-series data)
// ============================================================================
db.createCollection('sensor_readings');

// Crear índices para optimizar consultas
db.sensor_readings.createIndex({ "device_id": 1, "timestamp": -1 });
db.sensor_readings.createIndex({ "sensor_id": 1, "timestamp": -1 });
db.sensor_readings.createIndex({ "timestamp": -1 });
db.sensor_readings.createIndex({ "sensor_type": 1, "timestamp": -1 });

// ============================================================================
// COLECCIÓN: device_logs
// Descripción: Logs de eventos de dispositivos
// ============================================================================
db.createCollection('device_logs');

// Índices para logs
db.device_logs.createIndex({ "device_id": 1, "timestamp": -1 });
db.device_logs.createIndex({ "event_type": 1, "timestamp": -1 });
db.device_logs.createIndex({ "timestamp": -1 });

// ============================================================================
// COLECCIÓN: alerts
// Descripción: Alertas generadas por el sistema
// ============================================================================
db.createCollection('alerts');

// Índices para alertas
db.alerts.createIndex({ "device_id": 1, "timestamp": -1 });
db.alerts.createIndex({ "severity": 1, "resolved": 1 });
db.alerts.createIndex({ "timestamp": -1 });

// ============================================================================
// DATOS DE PRUEBA (Opcional)
// ============================================================================

// Insertar lecturas de ejemplo
db.sensor_readings.insertMany([
    {
        device_id: "DEV001",
        sensor_id: "SENS_TEMP_001",
        sensor_type: "temperature",
        timestamp: new Date(),
        value: 22.5,
        unit: "°C",
        quality: "good",
        metadata: {
            location: "Invernadero Principal",
            zone: "A1"
        }
    },
    {
        device_id: "DEV001",
        sensor_id: "SENS_HUM_001",
        sensor_type: "humidity",
        timestamp: new Date(),
        value: 65.3,
        unit: "%",
        quality: "good",
        metadata: {
            location: "Invernadero Principal",
            zone: "A1"
        }
    },
    {
        device_id: "DEV001",
        sensor_id: "SENS_CO2_001",
        sensor_type: "co2",
        timestamp: new Date(),
        value: 420,
        unit: "ppm",
        quality: "good",
        metadata: {
            location: "Invernadero Principal",
            zone: "A1"
        }
    }
]);

// Insertar log de ejemplo
db.device_logs.insertOne({
    device_id: "DEV001",
    timestamp: new Date(),
    event_type: "connection",
    severity: "info",
    message: "Device connected successfully",
    ip_address: "192.168.1.100",
    metadata: {
        firmware_version: "1.0.0",
        signal_strength: -45
    }
});

// Insertar alerta de ejemplo
db.alerts.insertOne({
    alert_id: "ALERT001",
    device_id: "DEV001",
    sensor_id: "SENS_TEMP_001",
    timestamp: new Date(),
    alert_type: "threshold_exceeded",
    severity: "warning",
    message: "Temperature above normal threshold",
    value: 35.2,
    threshold: 30.0,
    resolved: false,
    acknowledged: false
});

print("MongoDB initialization completed successfully");
print("Collections created: sensor_readings, device_logs, alerts");
print("Sample data inserted");
