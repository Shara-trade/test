-- ========================================================
-- ПУНКТ4. БАЗА ДАННЫХ (ПОЛНАЯ СТРУКТУРА)
-- Asteroid Miner - Полная схема базы данных
-- ========================================================

--4.1. Таблица users (пользователи)
CREATE TABLE IF NOT EXISTS users (
 user_id INTEGER PRIMARY KEY,
 username TEXT,
 first_name TEXT,
 last_name TEXT,
 
 -- Прогресс
 level INTEGER DEFAULT1,
 experience INTEGER DEFAULT0,
 prestige INTEGER DEFAULT0,
 tech_tokens INTEGER DEFAULT0,
 
-- Ресурсы
 metal INTEGER DEFAULT 0,
 crystals INTEGER DEFAULT 0,
 dark_matter INTEGER DEFAULT 0,
 energy INTEGER DEFAULT 1000,
 max_energy INTEGER DEFAULT 1000,
 credits INTEGER DEFAULT 0,
 quantum_tokens INTEGER DEFAULT 0,
 
 -- Состояние
 current_system TEXT DEFAULT 'alpha_7',
 heat INTEGER DEFAULT 0,
 heat_blocked_until TIMESTAMP DEFAULT NULL,
 total_clicks INTEGER DEFAULT 0,
 total_mined INTEGER DEFAULT 0,
 
 -- Служебные
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 referral_code TEXT UNIQUE,
 referred_by INTEGER DEFAULT NULL REFERENCES users(user_id),
 is_banned INTEGER DEFAULT 0,
 is_admin INTEGER DEFAULT 0
);

-- Индексы для users
CREATE INDEX IF NOT EXISTS idx_users_referral ON users(referral_code);
CREATE INDEX IF NOT EXISTS idx_users_referred ON users(referred_by);
CREATE INDEX IF NOT EXISTS idx_users_activity ON users(last_activity);

--4.2. Таблица drones (дроны)
CREATE TABLE IF NOT EXISTS drones (
 drone_id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
 drone_type TEXT NOT NULL, -- basic, miner, laser, quantum, ai
 level INTEGER DEFAULT1,
 income_per_tick INTEGER DEFAULT0,
 module_slots INTEGER DEFAULT1,
 installed_modules TEXT DEFAULT '[]', -- JSON массив
 is_active INTEGER DEFAULT1,
 acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_drones_user ON drones(user_id);

--4.3. Таблица inventory (инвентарь)
CREATE TABLE IF NOT EXISTS inventory (
 item_id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
 item_key TEXT NOT NULL, -- ссылка на items
 quantity INTEGER DEFAULT1,
 acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_inventory_user ON inventory(user_id);
CREATE INDEX IF NOT EXISTS idx_inventory_key ON inventory(item_key);

--4.3.1. Таблица user_modules (установленные модули)
CREATE TABLE IF NOT EXISTS user_modules (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
 item_key TEXT NOT NULL, -- ссылка на items (только type=module)
 installed_in TEXT DEFAULT NULL, -- NULL=в инвентаре, 'player'=на игроке, drone_id=на дроне
 slot_number INTEGER DEFAULT1,
 installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(user_id, item_key)
);

CREATE INDEX IF NOT EXISTS idx_user_modules_user ON user_modules(user_id);
CREATE INDEX IF NOT EXISTS idx_user_modules_installed ON user_modules(installed_in);

--4.4. Таблица items (справочник предметов)
CREATE TABLE IF NOT EXISTS items (
 item_key TEXT PRIMARY KEY,
 name TEXT NOT NULL,
 description TEXT,
 item_type TEXT NOT NULL, -- module, artifact, drone_blueprint, resource
 rarity TEXT NOT NULL, -- common, rare, epic, legendary, relic
 icon TEXT,
 max_stack INTEGER DEFAULT1,
 
 -- Эффекты (JSON)
 effects TEXT DEFAULT '{}', -- {"mining_bonus":5, "crit_chance":0.02}
 
 -- Требования для использования
 level_required INTEGER DEFAULT1,
 
 -- Можно ли продать
 can_sell INTEGER DEFAULT1,
 base_price INTEGER DEFAULT0
);

--4.5. Таблица market (рынок)
CREATE TABLE IF NOT EXISTS market (
 lot_id INTEGER PRIMARY KEY AUTOINCREMENT,
 seller_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
 item_key TEXT NOT NULL,
 quantity INTEGER DEFAULT1,
 price INTEGER NOT NULL, -- в кредитах
 status TEXT DEFAULT 'active', -- active, sold, cancelled
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 sold_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_market_seller ON market(seller_id);
CREATE INDEX IF NOT EXISTS idx_market_status ON market(status);
CREATE INDEX IF NOT EXISTS idx_market_item ON market(item_key);

--4.6. Таблица clans (кланы)
CREATE TABLE IF NOT EXISTS clans (
 clan_id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL UNIQUE,
 tag TEXT UNIQUE, -- [TAG]
 description TEXT,
 level INTEGER DEFAULT1,
 experience INTEGER DEFAULT0,
 leader_id INTEGER REFERENCES users(user_id),
 
 -- Статистика
 total_mining INTEGER DEFAULT0,
 members_count INTEGER DEFAULT0,
 max_members INTEGER DEFAULT20,
 
 -- Бонусы (JSON)
 active_buffs TEXT DEFAULT '{}',
 
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_clans_leader ON clans(leader_id);

--4.7. Таблица clan_members (участники кланов)
CREATE TABLE IF NOT EXISTS clan_members (
 member_id INTEGER PRIMARY KEY AUTOINCREMENT,
 clan_id INTEGER NOT NULL REFERENCES clans(clan_id) ON DELETE CASCADE,
 user_id INTEGER NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
 role TEXT DEFAULT 'member', -- member, officer, leader
 contribution INTEGER DEFAULT0,
 joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_clan_members_clan ON clan_members(clan_id);
CREATE INDEX IF NOT EXISTS idx_clan_members_user ON clan_members(user_id);

--4.8. Таблица clan_bosses (клановые боссы)
CREATE TABLE IF NOT EXISTS clan_bosses (
 boss_id INTEGER PRIMARY KEY AUTOINCREMENT,
 clan_id INTEGER NOT NULL REFERENCES clans(clan_id) ON DELETE CASCADE,
 boss_key TEXT NOT NULL,
 level INTEGER DEFAULT1,
 hp INTEGER NOT NULL,
 max_hp INTEGER NOT NULL,
 status TEXT DEFAULT 'active', -- active, defeated
 spawned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 defeated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_clan_bosses_clan ON clan_bosses(clan_id);

--4.9. Таблица daily_tasks (задания)
CREATE TABLE IF NOT EXISTS daily_tasks (
 task_id INTEGER PRIMARY KEY AUTOINCREMENT,
 task_key TEXT UNIQUE NOT NULL,
 name TEXT NOT NULL,
 description TEXT,
 task_type TEXT NOT NULL, -- mine, craft, sell, expedition
 target_value INTEGER NOT NULL,
 
 -- Награды
 reward_metal INTEGER DEFAULT0,
 reward_crystals INTEGER DEFAULT0,
 reward_credits INTEGER DEFAULT0,
 reward_item_key TEXT,
 
 -- Сложность
 difficulty TEXT DEFAULT 'easy', -- easy, medium, hard
 level_required INTEGER DEFAULT1
);

--4.10. Таблица user_tasks (прогресс заданий)
CREATE TABLE IF NOT EXISTS user_tasks (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
 task_id INTEGER NOT NULL REFERENCES daily_tasks(task_id),
 progress INTEGER DEFAULT0,
 completed INTEGER DEFAULT0,
 completed_at TIMESTAMP,
 assigned_date DATE DEFAULT CURRENT_DATE
);

CREATE INDEX IF NOT EXISTS idx_user_tasks_user ON user_tasks(user_id);

--4.11. Таблица containers (контейнеры)
CREATE TABLE IF NOT EXISTS containers (
 container_id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
 container_type TEXT NOT NULL, -- common, rare, epic, legendary
 status TEXT DEFAULT 'locked', -- locked, ready, opened
 unlock_time TIMESTAMP,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 opened_at TIMESTAMP,
 reward_data TEXT -- JSON с содержимым
);

CREATE INDEX IF NOT EXISTS idx_containers_user ON containers(user_id);

--4.12. Таблица expeditions (экспедиции)
CREATE TABLE IF NOT EXISTS expeditions (
 expedition_id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
 expedition_type TEXT NOT NULL, -- near_space, asteroid_belt, nebula
 drones_sent INTEGER DEFAULT1,
 status TEXT DEFAULT 'active', -- active, completed, cancelled
 start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 end_time TIMESTAMP,
 rewards_claimed INTEGER DEFAULT0,
 reward_data TEXT -- JSON с наградами
);

CREATE INDEX IF NOT EXISTS idx_expeditions_user ON expeditions(user_id);

--4.13. Таблица prestige_upgrades (престиж-улучшения)
CREATE TABLE IF NOT EXISTS prestige_upgrades (
 upgrade_id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
 upgrade_key TEXT NOT NULL,
 level INTEGER DEFAULT0,
 acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(user_id, upgrade_key)
);

CREATE INDEX IF NOT EXISTS idx_prestige_user ON prestige_upgrades(user_id);

--4.14. Таблица admin_logs (логи админов)
CREATE TABLE IF NOT EXISTS admin_logs (
 log_id INTEGER PRIMARY KEY AUTOINCREMENT,
 admin_id INTEGER NOT NULL REFERENCES users(user_id),
 action TEXT NOT NULL,
 target_user_id INTEGER,
 details TEXT,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_admin_logs_admin ON admin_logs(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_logs_date ON admin_logs(created_at);

--4.15. Таблица referrals (рефералы)
CREATE TABLE IF NOT EXISTS referrals (
 referral_id INTEGER PRIMARY KEY AUTOINCREMENT,
 referrer_id INTEGER NOT NULL REFERENCES users(user_id),
 referred_id INTEGER NOT NULL REFERENCES users(user_id),
 status TEXT DEFAULT 'pending', -- pending, active, completed
 reward_claimed INTEGER DEFAULT0,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(referrer_id, referred_id)
);

CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id);

-- Таблица для хранения статистики (для топов)
CREATE TABLE IF NOT EXISTS user_stats (
 stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
 weekly_mined INTEGER DEFAULT0,
 monthly_mined INTEGER DEFAULT0,
 total_items_found INTEGER DEFAULT0,
 total_crafted INTEGER DEFAULT0,
 total_sold INTEGER DEFAULT0,
 bosses_defeated INTEGER DEFAULT0,
 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Триггер для обновления updated_at
CREATE TRIGGER IF NOT EXISTS update_user_stats_timestamp 
AFTER UPDATE ON user_stats
BEGIN
 UPDATE user_stats SET updated_at = CURRENT_TIMESTAMP WHERE stat_id = NEW.stat_id;
END;

-- Инициализация базовых предметов
INSERT OR IGNORE INTO items (item_key, name, description, item_type, rarity, effects, base_price) VALUES
-- Обычные модули
('laser_mk1', 'Лазерный модуль Mk1', 'Стандартный лазер для добычи', 'module', 'common', '{"mining_bonus":5}',1000),
('battery_mk1', 'Батарея Mk1', 'Увеличивает запас энергии', 'module', 'common', '{"max_energy":100}',800),
('scanner_mk1', 'Сканер Mk1', 'Улучшает шанс найти предметы', 'module', 'common', '{"loot_chance":0.02}',1200),

-- Редкие модули
('laser_mk2', 'Лазерный модуль Mk2', 'Улучшенный лазер', 'module', 'rare', '{"mining_bonus":15}',5000),
('battery_mk2', 'Батарея Mk2', 'Мощная батарея', 'module', 'rare', '{"max_energy":300}',4000),
('turbine_mk1', 'Турбина Mk1', 'Ускоряет дронов', 'module', 'rare', '{"tick_reduction":0.1}',6000),

-- Эпические
('quantum_module', 'Квантовый модуль', 'Квантовые технологии', 'module', 'epic', '{"mining_bonus":50, "crit_chance":0.05}',25000),
('plasma_shield', 'Плазменный щит', 'Защита от перегрева', 'module', 'epic', '{"heat_reduction":5}',20000),

-- Артефакты
('ancient_engine', 'Древний двигатель', 'Технология древних', 'artifact', 'rare', '{"drone_power":10}',8000),
('ai_core', 'Ядро ИИ', 'Искусственный интеллект', 'artifact', 'rare', '{"crit_chance":0.03}',10000),
('alien_artifact', 'Инопланетный артефакт', 'Неизвестного происхождения', 'artifact', 'legendary', '{"mining_bonus":100}',100000),

-- Материалы (лут из добычи)
('scrap_metal', 'Металлолом', 'Обломки старых кораблей. Можно переработать.', 'material', 'common', '{}', 10),
('wires', 'Провода', 'Медные провода из старых систем.', 'material', 'common', '{}', 15),
('glass_shards', 'Осколки стекла', 'Остатки иллюминаторов.', 'material', 'common', '{}', 8),
('drone_parts', 'Детали дрона', 'Функциональные части старых дронов.', 'material', 'rare', '{}', 50),
('circuit_board', 'Плата', 'Рабочая электронная плата.', 'material', 'rare', '{}', 75),
('nano_core', 'Нано-ядро', 'Микроскопический процессор древней цивилизации.', 'artifact', 'epic', '{}', 500),
('quantum_chip', 'Квантовый чип', 'Улучшает крит-шанс на 1% при установке.', 'module', 'epic', '{"crit_chance":0.01}', 400),
('alien_alloy', 'Инопланетный сплав', 'Материал неизвестного происхождения. Очень ценный.', 'artifact', 'legendary', '{}', 2000),
('ai_fragment', 'Фрагмент ИИ', 'Часть древнего искусственного интеллекта.', 'artifact', 'legendary', '{}', 3000),

-- Расходники
('energy_cell', 'Энергоячейка', 'Заряженная батарея. Восстанавливает 50 энергии.', 'consumable', 'rare', '{"energy":50}', 100),
('energy_crystal', 'Кристалл энергии', 'Кристалл с чистой энергией. Восстанавливает 200 энергии.', 'consumable', 'epic', '{"energy":200}', 300);
