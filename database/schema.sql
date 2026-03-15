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
 level INTEGER DEFAULT 1,
 experience INTEGER DEFAULT 0,
 prestige INTEGER DEFAULT 0,
 tech_tokens INTEGER DEFAULT 0,
 
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
CREATE INDEX IF NOT EXISTS idx_users_level_exp ON users(level DESC, experience DESC);
CREATE INDEX IF NOT EXISTS idx_users_mined ON users(total_mined DESC);
CREATE INDEX IF NOT EXISTS idx_users_banned ON users(is_banned);

--4.2. Таблица drones (дроны)
CREATE TABLE IF NOT EXISTS drones (
 drone_id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
 drone_type TEXT NOT NULL, -- basic, miner, laser, quantum, ai
 level INTEGER DEFAULT 1,
 income_per_tick INTEGER DEFAULT 0,
 module_slots INTEGER DEFAULT 1,
 installed_modules TEXT DEFAULT '[]', -- JSON массив
 is_active INTEGER DEFAULT 1,
 acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_drones_user ON drones(user_id);

--4.3. Таблица inventory (инвентарь)
CREATE TABLE IF NOT EXISTS inventory (
 item_id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
 item_key TEXT NOT NULL, -- ссылка на items
 quantity INTEGER DEFAULT 1,
 acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_inventory_user ON inventory(user_id);
CREATE INDEX IF NOT EXISTS idx_inventory_key ON inventory(item_key);

--4.3.1. Таблица modules (генерируемые модули)
CREATE TABLE IF NOT EXISTS modules (
 module_id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
 name TEXT NOT NULL,           -- например: "Tr-12"
 rarity INTEGER DEFAULT 1,     -- 1=обычная, 2=редкая, 3=эпическая, 4=мифическая, 5=легендарная
 buffs TEXT NOT NULL,          -- JSON: {"asteroid_resources": 5.5, "container_chance": 3.5}
 debuffs TEXT NOT NULL,        -- JSON: {"resource_reduction": -11.0, "heat_per_click": 7.0}
 slot INTEGER DEFAULT NULL,    -- NULL=не надет, 1-4=номер слота
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_modules_user ON modules(user_id);
CREATE INDEX IF NOT EXISTS idx_modules_slot ON modules(slot);
CREATE INDEX IF NOT EXISTS idx_modules_rarity ON modules(rarity);

--4.4. Таблица items (справочник предметов)
CREATE TABLE IF NOT EXISTS items (
 item_key TEXT PRIMARY KEY,
 name TEXT NOT NULL,
 description TEXT,
 item_type TEXT NOT NULL, -- module, artifact, drone_blueprint, resource
 rarity TEXT NOT NULL, -- common, rare, epic, legendary, relic
 icon TEXT,
 max_stack INTEGER DEFAULT 1,
 
 -- Эффекты (JSON)
 effects TEXT DEFAULT '{}', -- {"mining_bonus":5, "crit_chance":0.02}
 
 -- Требования для использования
 level_required INTEGER DEFAULT 1,
 
 -- Можно ли продать
 can_sell INTEGER DEFAULT 1,
 base_price INTEGER DEFAULT 0
);

--4.5. Таблица market (рынок)
CREATE TABLE IF NOT EXISTS market (
 lot_id INTEGER PRIMARY KEY AUTOINCREMENT,
 seller_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
 item_key TEXT NOT NULL,
 quantity INTEGER DEFAULT 1,
 price INTEGER NOT NULL, -- в кредитах
 status TEXT DEFAULT 'active', -- active, sold, cancelled
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 sold_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_market_seller ON market(seller_id);
CREATE INDEX IF NOT EXISTS idx_market_status ON market(status);
CREATE INDEX IF NOT EXISTS idx_market_item ON market(item_key);
CREATE INDEX IF NOT EXISTS idx_market_active ON market(status, created_at DESC) WHERE status = 'active';

--4.6. Таблица clans (кланы)
CREATE TABLE IF NOT EXISTS clans (
 clan_id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL UNIQUE,
 tag TEXT UNIQUE, -- [TAG]
 description TEXT,
 level INTEGER DEFAULT 1,
 experience INTEGER DEFAULT 0,
 leader_id INTEGER REFERENCES users(user_id),
 
 -- Статистика
 total_mining INTEGER DEFAULT 0,
 members_count INTEGER DEFAULT 0,
 max_members INTEGER DEFAULT 20,
 
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
 contribution INTEGER DEFAULT 0,
 joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_clan_members_clan ON clan_members(clan_id);
CREATE INDEX IF NOT EXISTS idx_clan_members_user ON clan_members(user_id);

--4.8. Таблица clan_bosses (клановые боссы)
CREATE TABLE IF NOT EXISTS clan_bosses (
 boss_id INTEGER PRIMARY KEY AUTOINCREMENT,
 clan_id INTEGER NOT NULL REFERENCES clans(clan_id) ON DELETE CASCADE,
 boss_key TEXT NOT NULL,
 level INTEGER DEFAULT 1,
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
 reward_metal INTEGER DEFAULT 0,
 reward_crystals INTEGER DEFAULT 0,
 reward_credits INTEGER DEFAULT 0,
 reward_item_key TEXT,
 
 -- Сложность
 difficulty TEXT DEFAULT 'easy', -- easy, medium, hard
 level_required INTEGER DEFAULT 1
);

--4.10. Таблица user_tasks (прогресс заданий)
CREATE TABLE IF NOT EXISTS user_tasks (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
 task_id INTEGER NOT NULL REFERENCES daily_tasks(task_id),
 progress INTEGER DEFAULT 0,
 completed INTEGER DEFAULT 0,
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
CREATE INDEX IF NOT EXISTS idx_containers_status ON containers(status, unlock_time);

--4.12. Таблица expeditions (экспедиции)
CREATE TABLE IF NOT EXISTS expeditions (
 expedition_id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
 expedition_type TEXT NOT NULL, -- near_space, asteroid_belt, nebula
 drones_sent INTEGER DEFAULT 1,
 status TEXT DEFAULT 'active', -- active, completed, cancelled
 start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 end_time TIMESTAMP,
 rewards_claimed INTEGER DEFAULT 0,
 reward_data TEXT -- JSON с наградами
);

CREATE INDEX IF NOT EXISTS idx_expeditions_user ON expeditions(user_id);
CREATE INDEX IF NOT EXISTS idx_expeditions_status ON expeditions(status, end_time);

--4.13. Таблица prestige_upgrades (престиж-улучшения)
CREATE TABLE IF NOT EXISTS prestige_upgrades (
 upgrade_id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
 upgrade_key TEXT NOT NULL,
 level INTEGER DEFAULT 0,
 acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(user_id, upgrade_key)
);

CREATE INDEX IF NOT EXISTS idx_prestige_user ON prestige_upgrades(user_id);

--4.15. Таблица admin_logs (логи админов)
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

--4.16. Таблица admins (администраторы)
CREATE TABLE IF NOT EXISTS admins (
 admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
 role TEXT NOT NULL DEFAULT 'moderator',  -- owner, senior, moderator, support
 permissions TEXT DEFAULT '{}',           -- JSON с правами
 added_by INTEGER REFERENCES users(user_id),
 added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 is_active INTEGER DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_admins_user ON admins(user_id);
CREATE INDEX IF NOT EXISTS idx_admins_role ON admins(role);

--4.15. Таблица referrals (рефералы)
CREATE TABLE IF NOT EXISTS referrals (
 referral_id INTEGER PRIMARY KEY AUTOINCREMENT,
 referrer_id INTEGER NOT NULL REFERENCES users(user_id),
 referred_id INTEGER NOT NULL REFERENCES users(user_id),
 status TEXT DEFAULT 'pending', -- pending, active, completed
 reward_claimed INTEGER DEFAULT 0,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(referrer_id, referred_id)
);

CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id);

-- Таблица для хранения статистики (для топов)
CREATE TABLE IF NOT EXISTS user_stats (
 stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
 weekly_mined INTEGER DEFAULT 0,
 monthly_mined INTEGER DEFAULT 0,
 total_items_found INTEGER DEFAULT 0,
 total_crafted INTEGER DEFAULT 0,
 total_sold INTEGER DEFAULT 0,
 bosses_defeated INTEGER DEFAULT 0,
 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Триггер для обновления updated_at
CREATE TRIGGER IF NOT EXISTS update_user_stats_timestamp 
AFTER UPDATE ON user_stats
BEGIN
 UPDATE user_stats SET updated_at = CURRENT_TIMESTAMP WHERE stat_id = NEW.stat_id;
END;

-- ========================================================
-- АДМИН-ПАНЕЛЬ: ТАБЛИЦЫ НАСТРОЕК
-- ========================================================

-- 4.16. Таблица admin_settings (настройки админ-панели)
CREATE TABLE IF NOT EXISTS admin_settings (
    setting_key TEXT PRIMARY KEY,
    setting_value TEXT NOT NULL,
    setting_type TEXT DEFAULT 'json',  -- json, int, float, string, bool
    category TEXT DEFAULT 'general',   -- drop, economy, containers, modules, materials, limits
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_admin_settings_category ON admin_settings(category);

-- 4.17. Таблица admin_events (активные события)
CREATE TABLE IF NOT EXISTS admin_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,           -- container_drop, upgrade_discount, bonus_containers
    event_name TEXT NOT NULL,
    multiplier REAL DEFAULT 1.0,
    status TEXT DEFAULT 'active',       -- active, paused, completed
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ends_at TIMESTAMP,
    created_by INTEGER REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_admin_events_status ON admin_events(status);

-- 4.18. Таблица admin_backups (логи бэкапов)
CREATE TABLE IF NOT EXISTS admin_backups (
    backup_id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    file_size INTEGER DEFAULT 0,
    status TEXT DEFAULT 'created',      -- created, restored, failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(user_id)
);

-- 4.19. Таблица bans (баны игроков)
CREATE TABLE IF NOT EXISTS bans (
    ban_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    admin_id INTEGER NOT NULL REFERENCES users(user_id),
    reason TEXT,
    duration_hours INTEGER,             -- NULL = навсегда
    banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    unbanned_at TIMESTAMP,
    unbanned_by INTEGER REFERENCES users(user_id),
    status TEXT DEFAULT 'active'        -- active, expired, cancelled
);

CREATE INDEX IF NOT EXISTS idx_bans_user ON bans(user_id);
CREATE INDEX IF NOT EXISTS idx_bans_status ON bans(status);
CREATE INDEX IF NOT EXISTS idx_bans_expires ON bans(expires_at);

-- Инициализация базовых предметов
INSERT OR IGNORE INTO items (item_key, name, description, item_type, rarity, effects, base_price) VALUES
-- ===== МАТЕРИАЛЫ (Update.txt) =====
-- Группа 1 - Обычные
('asteroid_rock', 'Астероидная порода', 'Древняя порода из пояса астероидов.', 'material', 'common', '{}', 5),
('cosmic_silicon', 'Космический кремний', 'Чистый кремний из космических недр.', 'material', 'common', '{}', 8),
('metal_fragments', 'Металлические фрагменты', 'Обломки металлических конструкций.', 'material', 'common', '{}', 6),
('energy_condenser', 'Энергетический конденсатор', 'Накапливает и хранит энергию.', 'material', 'common', '{}', 15),
('quantum_fragment', 'Квантовый фрагмент', 'Частица квантового поля.', 'material', 'common', '{}', 25),

-- Группа 2 - Редкие
('xenotissue', 'Ксеноткань', 'Органическая ткань инопланетного происхождения.', 'material', 'rare', '{}', 50),
('plasma_core', 'Плазменное ядро', 'Стабилизированное плазменное образование.', 'material', 'rare', '{}', 80),
('astral_crystal', 'Астральный кристалл', 'Кристалл с астральной энергией.', 'material', 'rare', '{}', 100),
('gravity_node', 'Гравитационный узел', 'Узел гравитационных сил.', 'material', 'rare', '{}', 150),
('antimatter_capsule', 'Антиматериальная капсула', 'Капсула с антиматерией.', 'material', 'rare', '{}', 250),

-- Группа 3 - Эпические
('star_dust', 'Звёздная пыль', 'Пыль от погибших звёзд.', 'material', 'epic', '{}', 500),
('ion_module', 'Ионный модуль', 'Продвинутый ионный модуль.', 'material', 'epic', '{}', 600),
('ancient_nav_chip', 'Древний навигационный чип', 'Чип навигации древней цивилизации.', 'material', 'epic', '{}', 800),
('protoplanet_fragment', 'Фрагмент протопланеты', 'Осколок древней протопланеты.', 'material', 'epic', '{}', 1000),
('supernova_shard', 'Осколок сверхновой', 'Осколок взорвавшейся звезды.', 'material', 'epic', '{}', 2000),

-- ===== КОНТЕЙНЕРЫ =====
('container_common', 'Обычный контейнер', 'Контейнер с базовыми ресурсами.', 'container', 'common', '{}', 0),
('container_rare', 'Редкий контейнер', 'Контейнер с редкими ресурсами.', 'container', 'rare', '{}', 0),
('container_epic', 'Эпический контейнер', 'Контейнер с эпическими ресурсами.', 'container', 'epic', '{}', 0),
('container_mythic', 'Мифический контейнер', 'Контейнер с мифическими ресурсами.', 'container', 'mythic', '{}', 0),
('container_legendary', 'Легендарный контейнер', 'Контейнер с легендарными ресурсами.', 'container', 'legendary', '{}', 0),
('container_ksm', 'Контейнер с модулями', 'Специальный контейнер с модулями.', 'container', 'epic', '{}', 0);
    