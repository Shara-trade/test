-- Migration: add_performance_indexes
-- Created: 2025-01-14
-- Description: Добавляет индексы для оптимизации частых запросов

-- Индексы для топов и сортировки
CREATE INDEX IF NOT EXISTS idx_users_level_exp ON users(level DESC, experience DESC);
CREATE INDEX IF NOT EXISTS idx_users_mined ON users(total_mined DESC);
CREATE INDEX IF NOT EXISTS idx_users_banned ON users(is_banned);

-- Индекс для активных лотов рынка
CREATE INDEX IF NOT EXISTS idx_market_active ON market(status, created_at DESC);

-- Индекс для контейнеров по статусу
CREATE INDEX IF NOT EXISTS idx_containers_status ON containers(status, unlock_time);

-- Индекс для активных экспедиций
CREATE INDEX IF NOT EXISTS idx_expeditions_status ON expeditions(status, end_time);

-- Составной индекс для модулей пользователя со слотами
CREATE INDEX IF NOT EXISTS idx_modules_user_slot ON modules(user_id, slot);

-- Rollback (copy to rollback/001_add_performance_indexes.sql):
-- DROP INDEX IF EXISTS idx_users_level_exp;
-- DROP INDEX IF EXISTS idx_users_mined;
-- DROP INDEX IF EXISTS idx_users_banned;
-- DROP INDEX IF EXISTS idx_market_active;
-- DROP INDEX IF EXISTS idx_containers_status;
-- DROP INDEX IF EXISTS idx_expeditions_status;
-- DROP INDEX IF EXISTS idx_modules_user_slot;
