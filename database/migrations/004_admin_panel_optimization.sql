-- Migration: admin_panel_optimization
-- Created: 2025-01-14
-- Description: Индексы и поля для оптимизации админ-панели (пункт 6 ТЗ)

-- ==================== ИНДЕКСЫ ДЛЯ ПОИСКА ИГРОКОВ ====================

-- Индекс для поиска по username (регистронезависимый через LOWER)
CREATE INDEX IF NOT EXISTS idx_users_username_lower ON users(LOWER(username));

-- Индекс для поиска по имени
CREATE INDEX IF NOT EXISTS idx_users_first_name ON users(first_name);

-- Индекс для последней активности (онлайн, активные)
CREATE INDEX IF NOT EXISTS idx_users_last_activity ON users(last_activity DESC);

-- Составной индекс для фильтрации по уровню и активности
CREATE INDEX IF NOT EXISTS idx_users_level_activity ON users(level, last_activity DESC);

-- Индекс для поиска по дате регистрации
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);

-- ==================== ИНДЕКСЫ ДЛЯ АДМИН-ЛОГОВ ====================

-- Индекс для выборки логов по админу
CREATE INDEX IF NOT EXISTS idx_admin_logs_admin ON admin_logs(admin_id, created_at DESC);

-- Индекс для выборки логов по действию
CREATE INDEX IF NOT EXISTS idx_admin_logs_action ON admin_logs(action, created_at DESC);

-- Индекс для выборки логов по цели (история игрока)
CREATE INDEX IF NOT EXISTS idx_admin_logs_target ON admin_logs(target_user_id, created_at DESC);

-- Индекс для выборки логов по дате
CREATE INDEX IF NOT EXISTS idx_admin_logs_date ON admin_logs(created_at DESC);

-- ==================== ИНДЕКСЫ ДЛЯ БАНОВ ====================

-- Индекс для проверки активных банов
CREATE INDEX IF NOT EXISTS idx_bans_user_status ON bans(user_id, status);

-- Индекс для выборки по статусу
CREATE INDEX IF NOT EXISTS idx_bans_status ON bans(status);

-- Индекс для истечения банов
CREATE INDEX IF NOT EXISTS idx_bans_expires ON bans(expires_at) WHERE expires_at IS NOT NULL;

-- ==================== ИНДЕКСЫ ДЛЯ АДМИНОВ ====================

-- Индекс для проверки админки
CREATE INDEX IF NOT EXISTS idx_admins_user_active ON admins(user_id, is_active);

-- Индекс для выборки по роли
CREATE INDEX IF NOT EXISTS idx_admins_role ON admins(role);

-- ==================== ИНДЕКСЫ ДЛЯ СТАТИСТИКИ ====================

-- Индекс для подсчёта ресурсов
CREATE INDEX IF NOT EXISTS idx_users_resources ON users(metal, crystals, dark_matter);

-- Индекс для инвентаря (контейнеры)
CREATE INDEX IF NOT EXISTS idx_inventory_containers ON inventory(user_id, item_key) WHERE item_key LIKE 'container_%';

-- ==================== ДОБАВЛЕНИЕ ПОЛЕЙ АУДИТА ====================

-- Добавляем поля для аудита в admin_logs (если их нет)
-- SQLite не поддерживает IF NOT EXISTS для ALTER TABLE, поэтому используем безопасный подход

-- Попытка добавить колонки (игнорируем ошибку если уже существуют)
-- Выполняется через Python код в миграции

-- Создаём временную таблицу с нужной структурой
CREATE TABLE IF NOT EXISTS admin_logs_new (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    target_user_id INTEGER,
    details TEXT,
    old_value TEXT,  -- Старое значение (JSON)
    new_value TEXT,  -- Новое значение (JSON)
    ip_address TEXT, -- IP админа
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Копируем данные если таблица новая
INSERT OR IGNORE INTO admin_logs_new (log_id, admin_id, action, target_user_id, details, created_at)
SELECT log_id, admin_id, action, target_user_id, details, created_at FROM admin_logs;

-- Переименовываем таблицы (атомарная операция)
DROP TABLE IF EXISTS admin_logs;
ALTER TABLE admin_logs_new RENAME TO admin_logs;

-- Восстанавливаем индексы
CREATE INDEX IF NOT EXISTS idx_admin_logs_admin ON admin_logs(admin_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_admin_logs_action ON admin_logs(action, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_admin_logs_target ON admin_logs(target_user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_admin_logs_date ON admin_logs(created_at DESC);

-- ==================== ИНДЕКСЫ ДЛЯ НАСТРОЕК ====================

-- Индекс для быстрого поиска настроек
CREATE INDEX IF NOT EXISTS idx_admin_settings_key ON admin_settings(setting_key);

-- ==================== ИНДЕКСЫ ДЛЯ СОБЫТИЙ ====================

-- Индекс для активных событий
CREATE INDEX IF NOT EXISTS idx_admin_events_status ON admin_events(status, created_at DESC);

-- ==================== СТАТИСТИКА ИНДЕКСОВ ====================

-- После создания индексов анализируем таблицы для оптимизатора
ANALYZE;

-- Rollback (copy to rollback/004_admin_panel_optimization.sql):
-- DROP INDEX IF EXISTS idx_users_username_lower;
-- DROP INDEX IF EXISTS idx_users_first_name;
-- DROP INDEX IF EXISTS idx_users_last_activity;
-- DROP INDEX IF EXISTS idx_users_level_activity;
-- DROP INDEX IF EXISTS idx_users_created_at;
-- DROP INDEX IF EXISTS idx_admin_logs_admin;
-- DROP INDEX IF EXISTS idx_admin_logs_action;
-- DROP INDEX IF EXISTS idx_admin_logs_target;
-- DROP INDEX IF EXISTS idx_admin_logs_date;
-- DROP INDEX IF EXISTS idx_bans_user_status;
-- DROP INDEX IF EXISTS idx_bans_status;
-- DROP INDEX IF EXISTS idx_bans_expires;
-- DROP INDEX IF EXISTS idx_admins_user_active;
-- DROP INDEX IF EXISTS idx_admins_role;
-- DROP INDEX IF EXISTS idx_users_resources;
-- DROP INDEX IF EXISTS idx_inventory_containers;
-- DROP INDEX IF EXISTS idx_admin_settings_key;
-- DROP INDEX IF EXISTS idx_admin_events_status;
