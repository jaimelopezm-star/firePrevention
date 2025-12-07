-- Migration: Enable roles for managers (gerente)
-- Database: fire_preventionf

USE fire_preventionf;

-- 1) Add rol_id to gerente and create FK to rol(id) if missing
-- Add column rol_id only if it doesn't already exist (compatible con 8.0.x)
SET @col_exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'gerente' AND COLUMN_NAME = 'rol_id'
);
SET @sql := IF(@col_exists = 0,
  'ALTER TABLE gerente ADD COLUMN rol_id INT NULL',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Add FK only if it doesn't already exist
SET @fk_exists := (
  SELECT COUNT(*) FROM information_schema.REFERENTIAL_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = DATABASE() AND CONSTRAINT_NAME = 'fk_gerente_rol_id'
);
SET @sql := IF(@fk_exists = 0,
  'ALTER TABLE gerente ADD CONSTRAINT fk_gerente_rol_id FOREIGN KEY (rol_id) REFERENCES rol(id) ON DELETE SET NULL ON UPDATE CASCADE',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 2) Ensure role "manager" exists
INSERT INTO rol (nombre, description)
SELECT 'manager', 'Rol por defecto de gerentes'
WHERE NOT EXISTS (SELECT 1 FROM rol WHERE nombre='manager');

-- 3) Ensure baseline permissions for managers (adjust as needed)
-- You can modify this set to your needs
INSERT INTO permiso (name, description) VALUES
  ('view_reports', 'Ver reportes'),
  ('assign_device', 'Asignar dispositivos a servicios'),
  ('create_service', 'Crear servicios')
ON DUPLICATE KEY UPDATE description = VALUES(description);

-- Map those permissions to the manager role
INSERT INTO rol_permiso (role_id, permiso_id)
SELECT r.id, p.id
FROM rol r
JOIN permiso p ON p.name IN ('view_reports','assign_device','create_service')
WHERE r.nombre='manager'
ON DUPLICATE KEY UPDATE permiso_id = permiso_id;

-- 4) Assign role "manager" to existing gerente rows that have NULL rol_id
UPDATE gerente g
JOIN rol r ON r.nombre='manager'
SET g.rol_id = r.id
WHERE g.rol_id IS NULL;

-- Done.
