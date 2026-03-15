-- Rollback for: 001_add_performance_indexes
DROP INDEX IF EXISTS idx_users_level_exp;
DROP INDEX IF EXISTS idx_users_mined;
DROP INDEX IF EXISTS idx_users_banned;
DROP INDEX IF EXISTS idx_market_active;
DROP INDEX IF EXISTS idx_containers_status;
DROP INDEX IF EXISTS idx_expeditions_status;
DROP INDEX IF EXISTS idx_modules_user_slot;
