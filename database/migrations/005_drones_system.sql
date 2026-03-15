-- ========================================================
-- МИГРАЦИЯ 005: Новая система дронов
-- ========================================================

-- 1. Добавляем новые поля в таблицу users
ALTER TABLE users ADD COLUMN drones_hired INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE users ADD COLUMN hired_until TIMESTAMP DEFAULT NULL;
ALTER TABLE users ADD COLUMN storage_metal INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN storage_crystal INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN storage_dark INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN storage_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE users ADD COLUMN has_premium INTEGER DEFAULT 0;

-- 2. Создаём таблицу для хранения количества дронов по типам и уровням
CREATE TABLE IF NOT EXISTS user_drones (
    user_id INTEGER PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Базовый дрон
    base_lvl1 INTEGER DEFAULT 0,
    base_lvl2 INTEGER DEFAULT 0,
    base_lvl3 INTEGER DEFAULT 0,
    base_lvl4 INTEGER DEFAULT 0,
    base_lvl5 INTEGER DEFAULT 0,
    
    -- Шахтёр
    miner_lvl1 INTEGER DEFAULT 0,
    miner_lvl2 INTEGER DEFAULT 0,
    miner_lvl3 INTEGER DEFAULT 0,
    miner_lvl4 INTEGER DEFAULT 0,
    miner_lvl5 INTEGER DEFAULT 0,
    
    -- Лазерный
    laser_lvl1 INTEGER DEFAULT 0,
    laser_lvl2 INTEGER DEFAULT 0,
    laser_lvl3 INTEGER DEFAULT 0,
    laser_lvl4 INTEGER DEFAULT 0,
    laser_lvl5 INTEGER DEFAULT 0,
    
    -- Квантовый
    quantum_lvl1 INTEGER DEFAULT 0,
    quantum_lvl2 INTEGER DEFAULT 0,
    quantum_lvl3 INTEGER DEFAULT 0,
    quantum_lvl4 INTEGER DEFAULT 0,
    quantum_lvl5 INTEGER DEFAULT 0,
    
    -- ИИ-дрон
    ai_lvl1 INTEGER DEFAULT 0,
    ai_lvl2 INTEGER DEFAULT 0,
    ai_lvl3 INTEGER DEFAULT 0,
    ai_lvl4 INTEGER DEFAULT 0,
    ai_lvl5 INTEGER DEFAULT 0
);

-- Индексы для быстрого доступа
CREATE INDEX IF NOT EXISTS idx_user_drones_hired ON users(drones_hired);
CREATE INDEX IF NOT EXISTS idx_user_drones_hired_until ON users(hired_until);
