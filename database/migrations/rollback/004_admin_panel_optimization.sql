-- Rollback: admin_panel_optimization
-- Description: Откат миграции 004_admin_panel_optimization

-- Удаляем индексы
DROP INDEX IF EXISTS idx_users_username_lower;
DROP INDEX IF EXISTS idx_users_first_name;
DROP INDEX IF EXISTS idx_users_last_activity;
DROP INDEX IF EXISTS idx_users_level_activity;
DROP INDEX IF EXISTS idx_users_created_at;
DROP INDEX IF EXISTS idx_admin_logs_admin;
DROP INDEX IF EXISTS idx_admin_logs_action;
DROP INDEX IF EXISTS idx_admin_logs_target;
DROP INDEX IF EXISTS idx_admin_logs_date;
DROP INDEX IF EXISTS idx_bans_user_status;
DROP INDEX IF EXISTS idx_bans_status;
DROP INDEX IF EXISTS idx_bans_expires;
DROP INDEX IF EXISTS idx_admins_user_active;
DROP INDEX IF EXISTS idx_admins_role;
DROP INDEX IF EXISTS idx_users_resources;
DROP INDEX IF EXISTS idx_inventory_containers;
DROP INDEX IF EXISTS idx_admin_settings_key;
DROP INDEX IF EXISTS idx_admin_events_status;

-- Восстанавливаем старую структуру admin_logs
CREATE TABLE IF NOT EXISTS admin_logs_backup (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    target_user_id INTEGER,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO admin_logs_backup (log_id, admin_id, action, target_user_id, details, created_at)
SELECT log_id, admin_id, action, target_user_id, details, created_at FROM admin_logs;

DROP TABLE admin_logs;
ALTER TABLE admin_logs_backup RENAME TO admin_logs;
