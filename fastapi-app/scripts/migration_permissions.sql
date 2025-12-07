-- Migration: Add granular permissions and role assignments (no 'nivel' column)
-- Database: fire_preventionf

USE fire_preventionf;

-- 1) Insertar permisos faltantes (id autoincremental)
INSERT INTO permiso (name, description) VALUES
  ('create_manager', 'Crear nuevos gerentes'),
  ('edit_manager', 'Editar gerentes existentes'),
  ('delete_manager', 'Eliminar gerentes'),
  ('create_admin', 'Crear nuevos administradores'),
  ('manage_roles', 'Gestionar roles y permisos'),
  ('grant_permissions', 'Otorgar permisos a otros roles'),
  ('create_device', 'Crear dispositivos IoT'),
  ('edit_device', 'Editar dispositivos'),
  ('delete_device', 'Eliminar dispositivos'),
  ('view_all_users', 'Listar todos los usuarios')
ON DUPLICATE KEY UPDATE description = VALUES(description);

-- 2) Asignar permisos a admin_master (rol_id = 1)
INSERT INTO rol_permiso (role_id, permiso_id)
SELECT 1, p.id
FROM permiso p
WHERE p.name IN (
  'create_user','edit_user','delete_user',
  'create_service','assign_device','view_reports',
  'create_manager','edit_manager','delete_manager',
  'create_admin','manage_roles','grant_permissions',
  'create_device','edit_device','delete_device',
  'view_all_users'
)
ON DUPLICATE KEY UPDATE permiso_id = permiso_id;

-- 3) Asignar permisos a admin_normal (rol_id = 2)
INSERT INTO rol_permiso (role_id, permiso_id)
SELECT 2, p.id
FROM permiso p
WHERE p.name IN (
  'create_service','assign_device','view_reports'
)
ON DUPLICATE KEY UPDATE permiso_id = permiso_id;

-- 4) Limpieza de permisos indebidos en admin_normal
DELETE rp FROM rol_permiso rp
JOIN permiso p ON p.id = rp.permiso_id
WHERE rp.role_id = 2
AND p.name IN (
  'create_user','edit_user','delete_user',
  'create_admin','manage_roles','grant_permissions',
  'view_all_users',
  'create_device','edit_device','delete_device',
  'create_manager','edit_manager','delete_manager'
);

-- Nota: si deseas crear roles adicionales (manager, usuario_final), agrega aquí sus permisos.
-- Ejemplo (opcional):
-- INSERT INTO rol (nombre, description) VALUES ('manager', 'Gerente de servicios')
--   ON DUPLICATE KEY UPDATE description = VALUES(description);
-- INSERT INTO rol_permiso (role_id, permiso_id)
-- SELECT (SELECT id FROM rol WHERE nombre='manager'), p.id FROM permiso p
-- WHERE p.name IN ('create_service','assign_device','view_reports');

-- Fin de la migración.
