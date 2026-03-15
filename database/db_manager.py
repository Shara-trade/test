"""
Database Manager — менеджер базы данных.

Отвечает за все операции с базой данных SQLite:
- Создание и инициализация таблиц
- CRUD операции с пользователями, дронами, инвентарём, модулями
- Кэширование часто используемых данных
- Миграции схемы БД

Основные методы:
- get_user(user_id) — получить пользователя
- create_user(user_id, username) — создать пользователя
- update_user_resources(user_id, **kwargs) — обновить ресурсы
- add_experience(user_id, amount) — добавить опыт
- add_item(user_id, item_key, quantity) — добавить предмет в инвентарь
- get_user_full_profile(user_id) — получить полный профиль (оптимизировано)

Example:
    >>> from database import db_manager
    >>> user = await db_manager.get_user(123456789)
    >>> print(user['level'])
    5
"""
import aiosqlite
from typing import Optional, List, Dict
from datetime import datetime
from config import DATABASE_PATH
from .models import User, Drone, Item


class DatabaseManager:
    """
    Менеджер базы данных SQLite.
    
    Предоставляет асинхронный интерфейс для работы с БД.
    Все методы асинхронные и используют aiosqlite.
    
    Attributes:
        db_path (str): Путь к файлу базы данных
    
    Example:
        >>> db = DatabaseManager("asteroid_miner.db")
        >>> await db.init_db()
        >>> user = await db.get_user(123456789)
    """

    def __init__(self, db_path: str = DATABASE_PATH):
        """
        Инициализация менеджера БД.
        
        Args:
            db_path: Путь к файлу базы данных (по умолчанию из config.py)
        """
        self.db_path = db_path

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            with open("database/schema.sql", "r", encoding="utf-8") as f:
                await db.executescript(f.read())
            await db.commit()
            
            # Миграция: добавляем поле heat_blocked_until если его нет
            try:
                await db.execute("ALTER TABLE users ADD COLUMN heat_blocked_until TIMESTAMP DEFAULT NULL")
                await db.commit()
                print("Migration: added heat_blocked_until column")
            except:
                pass  # Колонка уже существует
                
            # Миграция: создаём таблицу admins если её нет
            try:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS admins (
                        admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
                        role TEXT NOT NULL DEFAULT 'moderator',
                        permissions TEXT DEFAULT '{}',
                        added_by INTEGER REFERENCES users(user_id),
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active INTEGER DEFAULT 1
                    )
                """)
                await db.execute("CREATE INDEX IF NOT EXISTS idx_admins_user ON admins(user_id)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_admins_role ON admins(role)")
                await db.commit()
                print("Migration: ensured admins table exists")
            except Exception as e:
                print(f"Migration admins table error: {e}")

            # Миграция: исправляем NULL значения на 0
            try:
                await db.execute("UPDATE users SET level = 1 WHERE level IS NULL")
                await db.execute("UPDATE users SET experience = 0 WHERE experience IS NULL")
                await db.execute("UPDATE users SET energy = 1000 WHERE energy IS NULL")
                await db.execute("UPDATE users SET max_energy = 1000 WHERE max_energy IS NULL")
                await db.execute("UPDATE users SET heat = 0 WHERE heat IS NULL")
                await db.commit()
                print("Migration: fixed NULL values to defaults")
            except Exception as e:
                print(f"Migration error: {e}")

            # Миграция: добавляем поля для новой системы дронов
            drone_fields = [
                ("drones_hired", "INTEGER DEFAULT 0"),
                ("last_update", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
                ("hired_until", "TIMESTAMP DEFAULT NULL"),
                ("storage_metal", "INTEGER DEFAULT 0"),
                ("storage_crystal", "INTEGER DEFAULT 0"),
                ("storage_dark", "INTEGER DEFAULT 0"),
                ("storage_updated", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
                ("has_premium", "INTEGER DEFAULT 0")
            ]
            
            for field_name, field_type in drone_fields:
                try:
                    await db.execute(f"ALTER TABLE users ADD COLUMN {field_name} {field_type}")
                    await db.commit()
                    print(f"Migration: added {field_name} column")
                except Exception as e:
                    if "duplicate column name" not in str(e).lower():
                        print(f"Migration {field_name} error: {e}")
            
            # Миграция: создаём таблицу user_drones
            try:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS user_drones (
                        user_id INTEGER PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
                        
                        base_lvl1 INTEGER DEFAULT 0, base_lvl2 INTEGER DEFAULT 0,
                        base_lvl3 INTEGER DEFAULT 0, base_lvl4 INTEGER DEFAULT 0, base_lvl5 INTEGER DEFAULT 0,
                        
                        miner_lvl1 INTEGER DEFAULT 0, miner_lvl2 INTEGER DEFAULT 0,
                        miner_lvl3 INTEGER DEFAULT 0, miner_lvl4 INTEGER DEFAULT 0, miner_lvl5 INTEGER DEFAULT 0,
                        
                        laser_lvl1 INTEGER DEFAULT 0, laser_lvl2 INTEGER DEFAULT 0,
                        laser_lvl3 INTEGER DEFAULT 0, laser_lvl4 INTEGER DEFAULT 0, laser_lvl5 INTEGER DEFAULT 0,
                        
                        quantum_lvl1 INTEGER DEFAULT 0, quantum_lvl2 INTEGER DEFAULT 0,
                        quantum_lvl3 INTEGER DEFAULT 0, quantum_lvl4 INTEGER DEFAULT 0, quantum_lvl5 INTEGER DEFAULT 0,
                        
                        ai_lvl1 INTEGER DEFAULT 0, ai_lvl2 INTEGER DEFAULT 0,
                        ai_lvl3 INTEGER DEFAULT 0, ai_lvl4 INTEGER DEFAULT 0, ai_lvl5 INTEGER DEFAULT 0
                    )
                """)
                await db.commit()
                print("Migration: created user_drones table")
            except Exception as e:
                print(f"Migration user_drones table error: {e}")

            # Инициализация администраторов из config.py (в том же соединении)
            await self._init_admins_internal(db)

            # Инициализация настроек админ-панели
            await self._init_settings_internal(db)

    async def _init_settings_internal(self, db):
        """Инициализация настроек админ-панели"""
        from admin.settings import DEFAULT_SETTINGS
        import json
        
        # Проверяем, есть ли настройки
        async with db.execute("SELECT COUNT(*) FROM admin_settings") as cursor:
            row = await cursor.fetchone()
            if row[0] > 0:
                return  # Настройки уже есть
        
        # Добавляем дефолтные настройки
        for key, definition in DEFAULT_SETTINGS.items():
            value_json = json.dumps(definition.default_value, ensure_ascii=False)
            await db.execute(
                """INSERT INTO admin_settings (setting_key, setting_value, setting_type, category, description)
                   VALUES (?, ?, ?, ?, ?)""",
                (key, value_json, definition.setting_type, definition.category, definition.description)
            )
        
        await db.commit()
        print(f"Initialized {len(DEFAULT_SETTINGS)} admin settings")

    async def _init_admins_internal(self, db):
        """Внутренний метод инициализации админов (вызывается внутри соединения)"""
        from config import ADMIN_IDS
        
        # Проверяем, есть ли админы в БД
        async with db.execute("SELECT COUNT(*) FROM admins") as cursor:
            row = await cursor.fetchone()
            if row[0] > 0:
                return  # Админы уже есть
        
        # Добавляем админов из config.py
        for i, admin_id in enumerate(ADMIN_IDS):
            if i == 0:
                role = 'owner'
            elif i == 1:
                role = 'senior'
            else:
                role = 'moderator'
            
            await db.execute(
                "INSERT OR IGNORE INTO admins (user_id, role, added_by) VALUES (?, ?, ?)",
                (admin_id, role, admin_id)
            )
        
        await db.commit()
        print(f"Initialized {len(ADMIN_IDS)} admins from config.py")

    async def init_admins(self):
        """Инициализация админов из config.py в БД (отдельный вызов)"""
        from config import ADMIN_IDS
        
        async with aiosqlite.connect(self.db_path) as db:
            # Проверяем, есть ли админы в БД
            async with db.execute("SELECT COUNT(*) FROM admins") as cursor:
                row = await cursor.fetchone()
                if row[0] > 0:
                    return  # Админы уже есть
            
            # Добавляем админов из config.py
            for i, admin_id in enumerate(ADMIN_IDS):
                if i == 0:
                    role = 'owner'
                elif i == 1:
                    role = 'senior'
                else:
                    role = 'moderator'
                
                await db.execute(
                    "INSERT OR IGNORE INTO admins (user_id, role, added_by) VALUES (?, ?, ?)",
                    (admin_id, role, admin_id)
                )
            
            await db.commit()
            print(f"Initialized {len(ADMIN_IDS)} admins from config.py")

    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Получить пользователя как словарь"""
        import logging
        logger = logging.getLogger("database")
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    data = dict(row)
                    data["is_banned"] = bool(data.get("is_banned", 0))
                    data["is_admin"] = bool(data.get("is_admin", 0))
                    
                    # Безопасные дефолты для None значений
                    if data.get("level") is None:
                        data["level"] = 1
                    if data.get("experience") is None:
                        data["experience"] = 0
                    if data.get("energy") is None:
                        data["energy"] = 1000
                    if data.get("max_energy") is None:
                        data["max_energy"] = 1000
                    if data.get("heat") is None:
                        data["heat"] = 0
                    if data.get("metal") is None:
                        data["metal"] = 0
                    if data.get("crystals") is None:
                        data["crystals"] = 0
                    if data.get("dark_matter") is None:
                        data["dark_matter"] = 0
                    if data.get("credits") is None:
                        data["credits"] = 0
                    if data.get("total_clicks") is None:
                        data["total_clicks"] = 0
                    if data.get("total_mined") is None:
                        data["total_mined"] = 0
                    
                    logger.debug(f"get_user({user_id}): level={data.get('level')}, exp={data.get('experience')}")
                    return data
                logger.warning(f"get_user({user_id}): user not found")
                return None
            
    async def create_user(self, user_id: int, username: str = None,
                          first_name: str = None, last_name: str = None) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            try:
                ref = f"REF{user_id}"
                await db.execute(
                    """INSERT INTO users (user_id, username, first_name, last_name, referral_code, 
                       level, experience, energy, max_energy, heat)
                       VALUES (?, ?, ?, ?, ?, 1, 0, 1000, 1000, 0)""",
                    (user_id, username, first_name, last_name, ref)
                )
                await db.commit()
                return True
            except Exception as e:
                print(f"Error: {e}")
                return False

    async def get_drones(self, user_id: int) -> List[Dict]:
        """Получить дроны пользователя как список словарей"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM drones WHERE user_id = ?", (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]
            
    async def get_item(self, item_key: str) -> Optional[Dict]:
        """Получить предмет как словарь"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM items WHERE item_key = ?", (item_key,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    # ==================== РЕСУРСЫ И СТАТИСТИКА ====================

    async def update_user_resources(self, user_id: int, **kwargs) -> bool:
        """Обновить ресурсы пользователя (инкремент/декремент)"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                updates = []
                values = []
                
                for key, value in kwargs.items():
                    if value > 0:
                        updates.append(f"{key} = {key} + ?")
                    else:
                        updates.append(f"{key} = MAX(0, {key} + ?)")
                    values.append(value)
                
                values.append(user_id)
                
                query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
                await db.execute(query, values)
                await db.commit()
                return True
            except Exception as e:
                print(f"Error updating resources: {e}")
                return False

    async def add_experience(self, user_id: int, amount: int) -> Dict:
        """Добавить опыт и проверить повышение уровня"""
        import logging
        logger = logging.getLogger("database")
        
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Получаем текущие данные
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT level, experience FROM users WHERE user_id = ?", (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if not row:
                        logger.error(f"User {user_id} not found in add_experience")
                        return {"success": False, "error": "User not found"}
                    
                    # Безопасное получение значений с обработкой None
                    current_level = row["level"] if row["level"] is not None else 1
                    current_exp = row["experience"] if row["experience"] is not None else 0
                
                logger.info(f"Adding {amount} exp to user {user_id}. Current: {current_exp}")
                
                # Добавляем опыт
                new_exp = current_exp + amount
                new_level = current_level
                levels_gained = 0
                
                # Проверяем повышение уровня
                while True:
                    exp_needed = self._exp_for_level(new_level)
                    if new_exp >= exp_needed:
                        new_exp -= exp_needed
                        new_level += 1
                        levels_gained += 1
                    else:
                        break
                
                # Обновляем в БД
                await db.execute(
                    "UPDATE users SET level = ?, experience = ? WHERE user_id = ?",
                    (new_level, new_exp, user_id)
                )
                
                # Увеличиваем макс. энергию за уровень
                if levels_gained > 0:
                    energy_bonus = levels_gained * 50
                    await db.execute(
                        "UPDATE users SET max_energy = max_energy + ? WHERE user_id = ?",
                        (energy_bonus, user_id)
                    )
                    logger.info(f"User {user_id} leveled up! New level: {new_level}")
                
                await db.commit()
                
                logger.info(f"Experience updated for user {user_id}: {current_exp} -> {new_exp}")
                
                return {
                    "success": True,
                    "old_level": current_level,
                    "new_level": new_level,
                    "levels_gained": levels_gained,
                    "exp_added": amount,
                    "current_exp": new_exp,
                    "exp_needed": self._exp_for_level(new_level)
                }
            except Exception as e:
                logger.error(f"Error adding experience for user {user_id}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return {"success": False, "error": str(e)}

    def _exp_for_level(self, level: int) -> int:
        """
        Опыт, необходимый для достижения уровня.

        Новая формула: 1000 * level * (1 + 0.1 * level)
        - Уровень 1: 1000 * 1 * 1.1 = 1100
        - Уровень 10: 1000 * 10 * 2.0 = 20000
        - Уровень 50: 1000 * 50 * 6.0 = 300000
        - Уровень 100: 1000 * 100 * 11.0 = 1100000
        
        Старая формула давала на 100 уровне ~8.2e9 опыта (слишком много).
        """
        return int(1000 * level * (1 + level * 0.1))

    async def update_heat(self, user_id: int, heat_change: int) -> Dict:
        """Обновить перегрев игрока"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Получаем текущий перегрев
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT heat FROM users WHERE user_id = ?", (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if not row:
                        return {"success": False}
                    
                    current_heat = row["heat"] if row["heat"] is not None else 0
                
                # Обновляем перегрев (0-100)
                new_heat = max(0, min(100, current_heat + heat_change))
                
                await db.execute(
                    "UPDATE users SET heat = ? WHERE user_id = ?",
                    (new_heat, user_id)
                )
                await db.commit()
                
                return {
                    "success": True,
                    "old_heat": current_heat,
                    "new_heat": new_heat,
                    "is_overheated": new_heat >= 100
                }
            except Exception as e:
                print(f"Error updating heat: {e}")
                return {"success": False}

    async def set_heat_block(self, user_id: int, seconds: int = 60) -> Dict:
        """Установить блокировку перегрева на N секунд"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                from datetime import datetime, timedelta
                
                blocked_until = datetime.now() + timedelta(seconds=seconds)
                
                await db.execute(
                    "UPDATE users SET heat = 100, heat_blocked_until = ? WHERE user_id = ?",
                    (blocked_until.isoformat(), user_id)
                )
                await db.commit()
                
                return {
                    "success": True,
                    "blocked_until": blocked_until.isoformat(),
                    "duration_seconds": seconds
                }
            except Exception as e:
                print(f"Error setting heat block: {e}")
                return {"success": False}

    async def get_heat_block_status(self, user_id: int) -> Dict:
        """Получить статус блокировки перегрева"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                from datetime import datetime
                
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT heat, heat_blocked_until FROM users WHERE user_id = ?", (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if not row:
                        return {"is_blocked": False}
                
                blocked_until_str = row["heat_blocked_until"]
                heat = row["heat"]
                
                if not blocked_until_str:
                    return {"is_blocked": False, "heat": heat}
                
                blocked_until = datetime.fromisoformat(blocked_until_str)
                now = datetime.now()
                
                if now < blocked_until:
                    remaining = int((blocked_until - now).total_seconds())
                    return {
                        "is_blocked": True,
                        "remaining_seconds": remaining,
                        "blocked_until": blocked_until_str,
                        "heat": heat
                    }
                else:
                    # Блокировка истекла, очищаем
                    await db.execute(
                        "UPDATE users SET heat_blocked_until = NULL WHERE user_id = ?",
                        (user_id,)
                    )
                    await db.commit()
                    return {"is_blocked": False, "heat": heat}
                    
            except Exception as e:
                print(f"Error getting heat block status: {e}")
                return {"is_blocked": False}

    async def clear_heat_block(self, user_id: int) -> bool:
        """Очистить блокировку перегрева"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "UPDATE users SET heat_blocked_until = NULL WHERE user_id = ?",
                    (user_id,)
                )
                await db.commit()
                return True
            except Exception as e:
                print(f"Error clearing heat block: {e}")
                return False

    async def clear_expired_heat_blocks(self) -> int:
        """
        Сбросить истёкшие блокировки перегрева.
        Устанавливает heat = 15 и очищает heat_blocked_until.
        
        Returns:
            Количество сброшенных блокировок
        """
        async with aiosqlite.connect(self.db_path) as db:
            try:
                from datetime import datetime
                
                now = datetime.now().isoformat()
                
                # Находим и обновляем пользователей с истёкшей блокировкой
                cursor = await db.execute("""
                    UPDATE users 
                    SET heat = 15, heat_blocked_until = NULL
                    WHERE heat_blocked_until IS NOT NULL 
                    AND heat_blocked_until <= ?
                    AND heat >= 100
                """, (now,))
                
                await db.commit()
                
                count = cursor.rowcount
                if count > 0:
                    print(f"Cleared {count} expired heat blocks")
                
                return count
            except Exception as e:
                print(f"Error clearing expired heat blocks: {e}")
                return 0

    async def check_and_clear_heat_block(self, user_id: int) -> Dict:
        """
        Проверить и очистить блокировку перегрева для конкретного пользователя.
        Если блокировка истекла - сбрасывает heat до 15.
        
        Returns:
            Статус блокировки и была ли она очищена
        """
        async with aiosqlite.connect(self.db_path) as db:
            try:
                from datetime import datetime
                
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT heat, heat_blocked_until FROM users WHERE user_id = ?", (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if not row:
                        return {"is_blocked": False, "was_cleared": False}
                
                blocked_until_str = row["heat_blocked_until"]
                heat = row["heat"]
                
                if not blocked_until_str:
                    return {"is_blocked": False, "heat": heat, "was_cleared": False}
                
                blocked_until = datetime.fromisoformat(blocked_until_str)
                now = datetime.now()
                
                if now < blocked_until:
                    remaining = int((blocked_until - now).total_seconds())
                    return {
                        "is_blocked": True,
                        "remaining_seconds": remaining,
                        "blocked_until": blocked_until_str,
                        "heat": heat,
                        "was_cleared": False
                    }
                else:
                    # Блокировка истекла - сбрасываем heat до 15
                    await db.execute(
                        "UPDATE users SET heat = 15, heat_blocked_until = NULL WHERE user_id = ?",
                        (user_id,)
                    )
                    await db.commit()
                
                    return {
                        "is_blocked": False,
                        "heat": 15,
                        "was_cleared": True,
                        "old_heat": heat
                    }
                    
            except Exception as e:
                print(f"Error checking heat block: {e}")
                return {"is_blocked": False, "was_cleared": False}

    async def update_last_activity(self, user_id: int):
        """Обновить время последней активности"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )
            await db.commit()

    async def fix_null_values(self, user_id: int = None):
        """Исправить NULL значения в базе данных"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Исправляем для конкретного пользователя или для всех
                if user_id:
                    await db.execute("""
                        UPDATE users SET 
                            level = COALESCE(level, 1),
                            experience = COALESCE(experience, 0),
                            energy = COALESCE(energy, 1000),
                            max_energy = COALESCE(max_energy, 1000),
                            heat = COALESCE(heat, 0),
                            metal = COALESCE(metal, 0),
                            crystals = COALESCE(crystals, 0),
                            dark_matter = COALESCE(dark_matter, 0),
                            credits = COALESCE(credits, 0),
                            total_clicks = COALESCE(total_clicks, 0),
                            total_mined = COALESCE(total_mined, 0)
                        WHERE user_id = ?
                    """, (user_id,))
                else:
                    await db.execute("""
                        UPDATE users SET 
                            level = COALESCE(level, 1),
                            experience = COALESCE(experience, 0),
                            energy = COALESCE(energy, 1000),
                            max_energy = COALESCE(max_energy, 1000),
                            heat = COALESCE(heat, 0),
                            metal = COALESCE(metal, 0),
                            crystals = COALESCE(crystals, 0),
                            dark_matter = COALESCE(dark_matter, 0),
                            credits = COALESCE(credits, 0),
                            total_clicks = COALESCE(total_clicks, 0),
                            total_mined = COALESCE(total_mined, 0)
                        WHERE level IS NULL OR experience IS NULL OR energy IS NULL
                    """)
                
                await db.commit()
                return True
            except Exception as e:
                print(f"Error fixing null values: {e}")
                return False

    async def get_user_stats(self, user_id: int) -> Optional[Dict]:
        """Получить полную статистику пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Основные данные
            async with db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ) as cursor:
                user_row = await cursor.fetchone()
                if not user_row:
                    return None
                user_data = dict(user_row)
            
            # Количество дронов
            async with db.execute(
                "SELECT COUNT(*) as count, SUM(income_per_tick) as total_income FROM drones WHERE user_id = ? AND is_active = 1",
                (user_id,)
            ) as cursor:
                drone_row = await cursor.fetchone()
                user_data["drones_count"] = drone_row["count"] or 0
                user_data["drones_income"] = drone_row["total_income"] or 0
            
            # Предметы в инвентаре
            async with db.execute(
                "SELECT COUNT(*) as count FROM inventory WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                item_row = await cursor.fetchone()
                user_data["items_count"] = item_row["count"] or 0
            
            return user_data

    async def get_user_full_profile(self, user_id: int) -> Optional[Dict]:
        """
        Получить полный профиль пользователя одним запросом.
        Оптимизированная версия для частого использования.
        
        Returns:
            Dict с данными пользователя и агрегированной статистикой
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Один запрос с подзапросами вместо 4 отдельных
            async with db.execute("""
                SELECT 
                    u.*,
                    (SELECT COUNT(*) FROM drones WHERE user_id = u.user_id AND is_active = 1) as drones_count,
                    (SELECT COALESCE(SUM(income_per_tick), 0) FROM drones WHERE user_id = u.user_id AND is_active = 1) as drones_income,
                    (SELECT COUNT(*) FROM inventory WHERE user_id = u.user_id AND quantity > 0) as items_count,
                    (SELECT COALESCE(SUM(quantity), 0) FROM inventory WHERE user_id = u.user_id) as items_total,
                    (SELECT COUNT(*) FROM inventory WHERE user_id = u.user_id AND item_key LIKE 'container_%' AND quantity > 0) as containers_count,
                    (SELECT COUNT(*) FROM modules WHERE user_id = u.user_id) as modules_count,
                    (SELECT COUNT(*) FROM modules WHERE user_id = u.user_id AND slot IS NOT NULL) as modules_installed
                FROM users u
                WHERE u.user_id = ?
            """, (user_id,)) as cursor:
                row = await cursor.fetchone()
                
                if not row:
                    return None
                
                data = dict(row)
                
                # Преобразуем булевы значения
                data["is_banned"] = bool(data.get("is_banned", 0))
                data["is_admin"] = bool(data.get("is_admin", 0))
                
                # Безопасные дефолты для None значений
                defaults = {
                    "level": 1, "experience": 0, "energy": 1000, "max_energy": 1000,
                    "heat": 0, "metal": 0, "crystals": 0, "dark_matter": 0,
                    "credits": 0, "total_clicks": 0, "total_mined": 0,
                    "drones_count": 0, "drones_income": 0, "items_count": 0,
                    "items_total": 0, "containers_count": 0, "modules_count": 0,
                    "modules_installed": 0
                }
                
                for key, default in defaults.items():
                    if data.get(key) is None:
                        data[key] = default
                
                return data

    async def get_user_cached(self, user_id: int, ttl: int = 30) -> Optional[Dict]:
        """
        Получить пользователя с кэшированием.
        Кэширует на указанное время (по умолчанию 30 сек).
        
        Args:
            user_id: ID пользователя
            ttl: Время жизни кэша в секундах
        
        Returns:
            Dict с данными пользователя
        """
        from core.cache import cache
        
        cache_key = f"user:{user_id}"
        cached = await cache.get(cache_key)
        
        if cached is not None:
            return cached
        
        user = await self.get_user(user_id)
        
        if user:
            await cache.set(cache_key, user, ttl=ttl)
        
        return user

    async def invalidate_user_cache(self, user_id: int):
        """Инвалидировать кэш пользователя"""
        from core.cache import cache
        
        await cache.delete(f"user:{user_id}")
        await cache.delete(f"module_bonuses:{user_id}")

    async def get_top_players(self, category: str = "level", limit: int = 10) -> List[Dict]:
        """Получить топ игроков"""
        order_columns = {
            "level": "level DESC, experience DESC",
            "mined": "total_mined DESC",
            "credits": "credits DESC",
            "clicks": "total_clicks DESC"
        }
        
        order_by = order_columns.get(category, "level DESC")
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                f"SELECT user_id, username, level, total_mined, credits, total_clicks FROM users WHERE is_banned = 0 ORDER BY {order_by} LIMIT ?",
                (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]
            
    async def get_user_rank(self, user_id: int, category: str = "level") -> int:
        """Получить ранг игрока в топе"""
        rank_queries = {
            "level": "SELECT COUNT(*) + 1 as rank FROM users WHERE (level > (SELECT level FROM users WHERE user_id = ?) OR (level = (SELECT level FROM users WHERE user_id = ?) AND experience > (SELECT experience FROM users WHERE user_id = ?))) AND is_banned = 0",
            "mined": "SELECT COUNT(*) + 1 as rank FROM users WHERE total_mined > (SELECT total_mined FROM users WHERE user_id = ?) AND is_banned = 0",
            "credits": "SELECT COUNT(*) + 1 as rank FROM users WHERE credits > (SELECT credits FROM users WHERE user_id = ?) AND is_banned = 0",
            "clicks": "SELECT COUNT(*) + 1 as rank FROM users WHERE total_clicks > (SELECT total_clicks FROM users WHERE user_id = ?) AND is_banned = 0"
        }
        
        query = rank_queries.get(category, rank_queries["level"])
        params = (user_id, user_id, user_id) if category == "level" else (user_id,)
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, params) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    # ==================== ИНВЕНТАРЬ ====================

    async def add_item(self, user_id: int, item_key: str, quantity: int = 1) -> Dict:
        """
        Добавить предмет в инвентарь.
        
        Args:
            user_id: ID пользователя
            item_key: Ключ предмета
            quantity: Количество для добавления
            
        Returns:
            Dict с ключами: success, error, item_id, quantity
        """
        import logging
        logger = logging.getLogger("database")
        
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Проверяем существование предмета в каталоге
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT item_key, name FROM items WHERE item_key = ?",
                    (item_key,)
                ) as cursor:
                    item_row = await cursor.fetchone()
                
                if not item_row:
                    logger.error(f"[add_item] Item '{item_key}' not found in items catalog")
                    return {
                        "success": False,
                        "error": f"Item '{item_key}' not found in items catalog",
                        "item_key": item_key
                    }
                
                # Проверяем, есть ли уже такой предмет у пользователя
                async with db.execute(
                    "SELECT item_id, quantity FROM inventory WHERE user_id = ? AND item_key = ?",
                    (user_id, item_key)
                ) as cursor:
                    row = await cursor.fetchone()
                
                if row:
                    # Увеличиваем количество
                    new_quantity = row["quantity"] + quantity
                    await db.execute(
                        "UPDATE inventory SET quantity = ? WHERE item_id = ?",
                        (new_quantity, row["item_id"])
                    )
                    item_id = row["item_id"]
                    logger.info(f"[add_item] Updated item '{item_key}' for user {user_id}: {row['quantity']} -> {new_quantity}")
                else:
                    # Добавляем новый предмет
                    cursor = await db.execute(
                        "INSERT INTO inventory (user_id, item_key, quantity) VALUES (?, ?, ?)",
                        (user_id, item_key, quantity)
                    )
                    item_id = cursor.lastrowid
                    logger.info(f"[add_item] Added new item '{item_key}' x{quantity} to user {user_id} inventory")
                
                await db.commit()
                
                return {
                    "success": True,
                    "item_id": item_id,
                    "item_key": item_key,
                    "quantity": quantity
                }
                
            except Exception as e:
                logger.error(f"[add_item] ERROR adding item '{item_key}' to user {user_id}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return {
                    "success": False,
                    "error": str(e),
                    "item_key": item_key,
                    "user_id": user_id
                }

    async def get_inventory(self, user_id: int) -> List[Dict]:
        """Получить инвентарь пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT i.item_id, i.item_key, i.quantity, 
                          COALESCE(it.name, i.item_key) as name,
                          COALESCE(it.rarity, 'common') as rarity,
                          COALESCE(it.icon, '📦') as icon
                   FROM inventory i 
                   LEFT JOIN items it ON i.item_key = it.item_key 
                   WHERE i.user_id = ? AND i.quantity > 0
                   ORDER BY 
                   CASE COALESCE(it.rarity, 'common')
                       WHEN 'legendary' THEN 1
                       WHEN 'epic' THEN 2
                       WHEN 'rare' THEN 3
                       ELSE 4
                   END""",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]
            
    # ==================== КОНТЕЙНЕРЫ ====================

    async def add_container(self, user_id: int, container_type: str) -> Dict:
        """Добавить контейнер пользователю"""
        from datetime import datetime, timedelta
        from game import container_system
        
        container_info = container_system.get_container_by_type(container_type)
        if not container_info:
            return {"success": False, "error": "Unknown container type"}
        
        unlock_time = datetime.now() + timedelta(minutes=container_info.unlock_minutes)
        
        async with aiosqlite.connect(self.db_path) as db:
            try:
                cursor = await db.execute(
                    """INSERT INTO containers (user_id, container_type, status, unlock_time)
                       VALUES (?, ?, 'locked', ?)""",
                    (user_id, container_type, unlock_time.isoformat())
                )
                await db.commit()
                
                return {
                    "success": True,
                    "container_id": cursor.lastrowid,
                    "container_type": container_type,
                    "unlock_time": unlock_time.isoformat()
                }
            except Exception as e:
                print(f"Error adding container: {e}")
                return {"success": False, "error": str(e)}

    async def get_user_containers(self, user_id: int) -> List[Dict]:
        """Получить контейнеры пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT container_id, container_type, status, unlock_time, created_at
                   FROM containers 
                   WHERE user_id = ? AND status != 'opened'
                   ORDER BY unlock_time ASC""",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_containers_count(self, user_id: int) -> int:
        """Получить количество контейнеров пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM containers WHERE user_id = ? AND status != 'opened'",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    # ==================== РАСШИРЕННЫЕ МЕТОДЫ ИНВЕНТАРЯ ====================

    async def get_user_inventory(self, user_id: int) -> List[Dict]:
        """Получить инвентарь пользователя с полной информацией о предметах"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT 
                    i.item_id, 
                    i.item_key, 
                    i.quantity,
                    i.acquired_at,
                    COALESCE(it.name, i.item_key) as name,
                    COALESCE(it.description, '') as description,
                    COALESCE(it.item_type, 'resource') as item_type,
                    COALESCE(it.rarity, 'common') as rarity,
                    COALESCE(it.icon, '📦') as icon,
                    COALESCE(it.max_stack, 999) as max_stack,
                    COALESCE(it.effects, '{}') as effects,
                    COALESCE(it.can_sell, 1) as can_sell,
                    COALESCE(it.base_price, 0) as base_price,
                    COALESCE(it.level_required, 1) as level_required
                   FROM inventory i 
                   LEFT JOIN items it ON i.item_key = it.item_key 
                   WHERE i.user_id = ? AND i.quantity > 0
                   ORDER BY 
                   CASE COALESCE(it.rarity, 'common')
                       WHEN 'relic' THEN 1
                       WHEN 'legendary' THEN 2
                       WHEN 'epic' THEN 3
                       WHEN 'rare' THEN 4
                       ELSE 5
                   END, i.quantity DESC""",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_item_info(self, item_key: str) -> Optional[Dict]:
        """Получить информацию о предмете из каталога"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM items WHERE item_key = ?",
                (item_key,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_user_item(self, user_id: int, item_key: str) -> Optional[Dict]:
        """Получить конкретный предмет пользователя с информацией"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT 
                    i.item_id, 
                    i.item_key, 
                    i.quantity,
                    i.acquired_at,
                    COALESCE(it.name, i.item_key) as name,
                    COALESCE(it.description, '') as description,
                    COALESCE(it.item_type, 'resource') as item_type,
                    COALESCE(it.rarity, 'common') as rarity,
                    COALESCE(it.icon, '📦') as icon,
                    COALESCE(it.max_stack, 999) as max_stack,
                    COALESCE(it.effects, '{}') as effects,
                    COALESCE(it.can_sell, 1) as can_sell,
                    COALESCE(it.base_price, 0) as base_price,
                    COALESCE(it.level_required, 1) as level_required
                   FROM inventory i 
                   LEFT JOIN items it ON i.item_key = it.item_key 
                   WHERE i.user_id = ? AND i.item_key = ?""",
                (user_id, item_key)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def remove_item(self, user_id: int, item_key: str, quantity: int = 1) -> bool:
        """Удалить предмет из инвентаря"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Получаем текущее количество
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT item_id, quantity FROM inventory WHERE user_id = ? AND item_key = ?",
                    (user_id, item_key)
                ) as cursor:
                    row = await cursor.fetchone()
                
                if not row:
                    return False
                
                new_quantity = row["quantity"] - quantity
                
                if new_quantity <= 0:
                    # Удаляем запись
                    await db.execute(
                        "DELETE FROM inventory WHERE item_id = ?",
                        (row["item_id"],)
                    )
                else:
                    # Уменьшаем количество
                    await db.execute(
                        "UPDATE inventory SET quantity = ? WHERE item_id = ?",
                        (new_quantity, row["item_id"])
                    )
                
                await db.commit()
                return True
            except Exception as e:
                print(f"Error removing item: {e}")
                return False

    async def get_inventory_stats(self, user_id: int) -> Dict:
        """Получить статистику инвентаря"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Общее количество предметов
            async with db.execute(
                "SELECT COUNT(*) as count, SUM(quantity) as total FROM inventory WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                total_items = row["count"] or 0
                total_quantity = row["total"] or 0
            
            # По редкости
            async with db.execute(
                """SELECT 
                    COALESCE(it.rarity, 'common') as rarity,
                    SUM(i.quantity) as count
                   FROM inventory i 
                   LEFT JOIN items it ON i.item_key = it.item_key 
                   WHERE i.user_id = ?
                   GROUP BY it.rarity""",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                by_rarity = {row["rarity"]: row["count"] for row in rows}
            
            # Общая стоимость
            async with db.execute(
                """SELECT SUM(i.quantity * COALESCE(it.base_price, 0)) as total_value
                   FROM inventory i 
                   LEFT JOIN items it ON i.item_key = it.item_key 
                   WHERE i.user_id = ?""",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                total_value = row["total_value"] or 0
            
            return {
                "total_items": total_items,
                "total_quantity": total_quantity,
                "by_rarity": by_rarity,
                "total_value": total_value
            }

    # ==================== КОНТЕЙНЕРЫ (РАСШИРЕНО) ====================

    async def open_container(self, user_id: int, container_id: int) -> Optional[Dict]:
        """Открыть контейнер и получить награды"""
        from datetime import datetime
        from game import container_system
        import random
        import json
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Получаем контейнер
            async with db.execute(
                "SELECT * FROM containers WHERE container_id = ? AND user_id = ?",
                (container_id, user_id)
            ) as cursor:
                row = await cursor.fetchone()
            
            if not row:
                return None
            
            container = dict(row)
            container_type = container["container_type"]
            status = container["status"]
            unlock_time_str = container.get("unlock_time")
            
            # Проверяем статус
            if status == "opened":
                return None
            
            # Проверяем время если locked
            if status == "locked" and unlock_time_str:
                try:
                    unlock_time = datetime.fromisoformat(unlock_time_str)
                    if datetime.now() < unlock_time:
                        return {
                            "success": False,
                            "error": "not_ready",
                            "unlock_time": unlock_time_str
                        }
                except:
                    pass
            
            # Получаем информацию о контейнере
            container_info = container_system.get_container_by_type(container_type)
            if not container_info:
                return None
            
            # Генерируем награды
            result = container_system.generate_rewards(container_info)
            rewards = result.get("rewards", [])
            
            # Добавляем награды пользователю
            for reward in rewards:
                reward_type = reward.get("type")
                
                if reward_type == "item":
                    item_key = reward.get("item_key")
                    quantity = reward.get("quantity", 1)
                    await self.add_item(user_id, item_key, quantity)
                
                elif reward_type == "resource":
                    resource = reward.get("resource")
                    quantity = reward.get("quantity", 0)
                    if resource in ["metal", "crystals", "dark_matter", "credits", "energy"]:
                        await self.update_user_resources(user_id, **{resource: quantity})
            
            # Помечаем контейнер как открытый
            await db.execute(
                "UPDATE containers SET status = 'opened', opened_at = ? WHERE container_id = ?",
                (datetime.now().isoformat(), container_id)
            )
            await db.commit()
            
            return {
                "success": True,
                "container_id": container_id,
                "container_type": container_type,
                "rewards": rewards
            }

    async def update_container_status(self, user_id: int = None) -> int:
        """Обновить статус контейнеров (locked -> ready)"""
        from datetime import datetime
        
        async with aiosqlite.connect(self.db_path) as db:
            now = datetime.now().isoformat()
            
            if user_id:
                cursor = await db.execute(
                    "UPDATE containers SET status = 'ready' WHERE user_id = ? AND status = 'locked' AND unlock_time <= ?",
                    (user_id, now)
                )
            else:
                cursor = await db.execute(
                    "UPDATE containers SET status = 'ready' WHERE status = 'locked' AND unlock_time <= ?",
                    (now,)
                )
            
            await db.commit()
            return cursor.rowcount

    # ==================== МОДУЛИ (modules table) ====================

    async def create_module(self, user_id: int, name: str, rarity: int, buffs: Dict, debuffs: Dict) -> Dict:
        """
        Создать новый модуль.
        
        Returns:
            Dict с ключами: success, module_id, name, rarity, buffs, debuffs
        """
        import json
        
        async with aiosqlite.connect(self.db_path) as db:
            try:
                cursor = await db.execute(
                    """INSERT INTO modules (user_id, name, rarity, buffs, debuffs)
                       VALUES (?, ?, ?, ?, ?)""",
                    (user_id, name, rarity, json.dumps(buffs), json.dumps(debuffs))
                )
                await db.commit()
                
                return {
                    "success": True,
                    "module_id": cursor.lastrowid,
                    "name": name,
                    "rarity": rarity,
                    "buffs": buffs,
                    "debuffs": debuffs
                }
            except Exception as e:
                print(f"Error creating module: {e}")
                return {"success": False, "error": str(e)}

    async def get_user_modules(self, user_id: int) -> List[Dict]:
        """Получить все модули пользователя"""
        import json
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            async with db.execute(
                """SELECT module_id, name, rarity, buffs, debuffs, slot, created_at
                   FROM modules WHERE user_id = ?
                   ORDER BY rarity DESC, module_id ASC""",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                
                modules = []
                for row in rows:
                    module = dict(row)
                    # Парсим JSON поля
                    if isinstance(module.get('buffs'), str):
                        module['buffs'] = json.loads(module['buffs'])
                    if isinstance(module.get('debuffs'), str):
                        module['debuffs'] = json.loads(module['debuffs'])
                    modules.append(module)
                
                return modules

    async def get_module_by_id(self, user_id: int, module_id: int) -> Optional[Dict]:
        """Получить модуль по ID"""
        import json
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            async with db.execute(
                """SELECT module_id, name, rarity, buffs, debuffs, slot, created_at
                   FROM modules WHERE module_id = ? AND user_id = ?""",
                (module_id, user_id)
            ) as cursor:
                row = await cursor.fetchone()
                
                if not row:
                    return None
                
                module = dict(row)
                if isinstance(module.get('buffs'), str):
                    module['buffs'] = json.loads(module['buffs'])
                if isinstance(module.get('debuffs'), str):
                    module['debuffs'] = json.loads(module['debuffs'])
                
                return module

    async def get_installed_modules_by_slots(self, user_id: int) -> Dict[int, Dict]:
        """Получить установленные модули по слотам"""
        import json
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            async with db.execute(
                """SELECT module_id, name, rarity, buffs, debuffs, slot
                   FROM modules WHERE user_id = ? AND slot IS NOT NULL""",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                
                result = {}
                for row in rows:
                    module = dict(row)
                    if isinstance(module.get('buffs'), str):
                        module['buffs'] = json.loads(module['buffs'])
                    if isinstance(module.get('debuffs'), str):
                        module['debuffs'] = json.loads(module['debuffs'])
                    result[module['slot']] = module
                
                return result

    async def install_module_to_slot(self, user_id: int, module_id: int, slot: int) -> bool:
        """Установить модуль в слот"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Проверяем, что слот свободен
                async with db.execute(
                    "SELECT module_id FROM modules WHERE user_id = ? AND slot = ?",
                    (user_id, slot)
                ) as cursor:
                    if await cursor.fetchone():
                        return False
                
                # Проверяем, что модуль не установлен в другом слоте
                async with db.execute(
                    "SELECT slot FROM modules WHERE module_id = ? AND user_id = ?",
                    (module_id, user_id)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row and row['slot'] is not None:
                        return False
                
                # Устанавливаем
                await db.execute(
                    "UPDATE modules SET slot = ? WHERE module_id = ? AND user_id = ?",
                    (slot, module_id, user_id)
                )
                await db.commit()
                return True
            except Exception as e:
                print(f"Error installing module: {e}")
                return False

    async def uninstall_module_from_slot(self, user_id: int, module_id: int) -> bool:
        """Снять модуль со слота"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "UPDATE modules SET slot = NULL WHERE module_id = ? AND user_id = ?",
                    (module_id, user_id)
                )
                await db.commit()
                return True
            except Exception as e:
                print(f"Error uninstalling module: {e}")
                return False

    async def update_module(self, user_id: int, module_id: int, data: Dict) -> bool:
        """Обновить модуль (улучшение)"""
        import json
        
        async with aiosqlite.connect(self.db_path) as db:
            try:
                rarity = data.get('rarity')
                buffs = data.get('buffs', {})
                debuffs = data.get('debuffs', {})
                
                await db.execute(
                    """UPDATE modules 
                       SET rarity = ?, buffs = ?, debuffs = ?
                       WHERE module_id = ? AND user_id = ?""",
                    (rarity, json.dumps(buffs), json.dumps(debuffs), module_id, user_id)
                )
                await db.commit()
                return True
            except Exception as e:
                print(f"Error updating module: {e}")
                return False

    async def delete_module(self, user_id: int, module_id: int) -> bool:
        """Удалить модуль (продажа/разборка)"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "DELETE FROM modules WHERE module_id = ? AND user_id = ?",
                    (module_id, user_id)
                )
                await db.commit()
                return True
            except Exception as e:
                print(f"Error deleting module: {e}")
                return False

    async def get_modules_count(self, user_id: int) -> int:
        """Получить количество модулей пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM modules WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_active_module_bonuses(self, user_id: int) -> Dict:
        """
        Получить бонусы от установленных модулей (из новой таблицы modules).
        Суммирует все бафы и дебафы установленных модулей.

        Returns:
            Dict с бонусами, например:
            {
                'asteroid_resources': 5.5,
                'rare_asteroid_chance': 2.5,
                'max_energy': 120,
                'heat_per_click': -7.0,
                ...
            }
        """
        import json
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Получаем все установленные модули
            async with db.execute(
                """SELECT buffs, debuffs FROM modules WHERE user_id = ? AND slot IS NOT NULL""",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
            
            # Суммируем бонусы
            total_bonuses = {}
            
            for row in rows:
                # Парсим бафы
                buffs = row["buffs"]
                if isinstance(buffs, str):
                    buffs = json.loads(buffs)
                
                if buffs:
                    for key, value in buffs.items():
                        if key in total_bonuses:
                            total_bonuses[key] += value
                        else:
                            total_bonuses[key] = value
                
                # Парсим дебафы
                debuffs = row["debuffs"]
                if isinstance(debuffs, str):
                    debuffs = json.loads(debuffs)
                
                if debuffs:
                    for key, value in debuffs.items():
                        if key in total_bonuses:
                            total_bonuses[key] -= value  # Дебафы вычитаем
                        else:
                            total_bonuses[key] = -value
            
            return total_bonuses

    # ==================== СИСТЕМА ДРОНОВ (НОВАЯ) ====================

    async def get_user_drones(self, user_id: int) -> Dict:
        """
        Получить данные о дронах пользователя.
        
        Returns:
            Dict с полями: base_lvl1...ai_lvl5, drones_hired, hired_until, 
            storage_metal, storage_crystal, storage_dark, has_premium
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Получаем данные пользователя
            async with db.execute(
                """SELECT drones_hired, hired_until, last_update,
                          storage_metal, storage_crystal, storage_dark, 
                          storage_updated, has_premium
                   FROM users WHERE user_id = ?""",
                (user_id,)
            ) as cursor:
                user_row = await cursor.fetchone()
            
            if not user_row:
                return {}
            
            result = dict(user_row)
            
            # Получаем количество дронов
            async with db.execute(
                "SELECT * FROM user_drones WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                drones_row = await cursor.fetchone()
            
            if drones_row:
                result.update(dict(drones_row))
            else:
                # Создаём запись если нет
                await db.execute(
                    "INSERT OR IGNORE INTO user_drones (user_id) VALUES (?)",
                    (user_id,)
                )
                await db.commit()
                
                # Заполняем нулями
                for dtype in ['base', 'miner', 'laser', 'quantum', 'ai']:
                    for lvl in range(1, 6):
                        result[f"{dtype}_lvl{lvl}"] = 0
            
            return result

    async def update_user_drones(self, user_id: int, updates: Dict) -> bool:
        """
        Обновить количество дронов пользователя.
        
        Args:
            updates: Dict с полями типа base_lvl1, miner_lvl2 и т.д.
        """
        async with aiosqlite.connect(self.db_path) as db:
            try:
                set_clauses = []
                values = []
                
                for key, value in updates.items():
                    if key.endswith('_lvl1') or key.endswith('_lvl2') or key.endswith('_lvl3') or \
                       key.endswith('_lvl4') or key.endswith('_lvl5'):
                        set_clauses.append(f"{key} = MAX(0, {key} + ?)")
                        values.append(value)
                
                if not set_clauses:
                    return True
                
                values.append(user_id)
                
                query = f"UPDATE user_drones SET {', '.join(set_clauses)} WHERE user_id = ?"
                await db.execute(query, values)
                await db.commit()
                return True
            except Exception as e:
                print(f"Error updating drones: {e}")
                return False

    async def buy_drone(self, user_id: int, drone_type: str, count: int = 1) -> Dict:
        """
        Купить дронов 1 уровня.
        
        Returns:
            Dict с ключами: success, error, count
        """
        from game.drones import DRONE_CONFIG
        
        config = DRONE_CONFIG.get(drone_type)
        if not config:
            return {"success": False, "error": "Неизвестный тип дрона"}
        
        price = config['price']
        
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Проверяем баланс
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT metal, crystals, dark_matter FROM users WHERE user_id = ?",
                    (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                
                if not row:
                    return {"success": False, "error": "Пользователь не найден"}
                
                # Сколько можем купить
                max_by_metal = row['metal'] // price['metal'] if price['metal'] > 0 else count
                max_by_crystals = row['crystals'] // price['crystals'] if price['crystals'] > 0 else count
                max_by_dark = row['dark_matter'] // price['dark_matter'] if price['dark_matter'] > 0 else count
                
                can_buy = min(count, max_by_metal, max_by_crystals, max_by_dark)
                
                if can_buy == 0:
                    return {"success": False, "error": "Недостаточно ресурсов"}
                
                # Списываем ресурсы
                total_price = {
                    'metal': price['metal'] * can_buy,
                    'crystals': price['crystals'] * can_buy,
                    'dark_matter': price['dark_matter'] * can_buy
                }
                
                await db.execute(
                    """UPDATE users SET 
                       metal = metal - ?,
                       crystals = crystals - ?,
                       dark_matter = dark_matter - ?
                       WHERE user_id = ?""",
                    (total_price['metal'], total_price['crystals'], total_price['dark_matter'], user_id)
                )
                
                # Добавляем дронов
                key = f"{drone_type}_lvl1"
                await db.execute(
                    f"INSERT INTO user_drones (user_id, {key}) VALUES (?, ?) "
                    f"ON CONFLICT(user_id) DO UPDATE SET {key} = {key} + ?",
                    (user_id, can_buy, can_buy)
                )
                
                await db.commit()
                
                return {
                    "success": True,
                    "count": can_buy,
                    "total_price": total_price
                }
            except Exception as e:
                print(f"Error buying drone: {e}")
                return {"success": False, "error": str(e)}

    async def hire_drone(self, user_id: int, drone_type: str, level: int, count: int = 1) -> Dict:
        """
        Нанять дронов (перевести в найм).
        
        Note: В ТЗ дроны не перемещаются между таблицами, 
        drones_hired = общее количество работающих.
        Для упрощения считаем что все дроны в ангаре = свободные.
        
        Returns:
            Dict с ключами: success, error, count
        """
        from game.drones import MAX_HIRED_DRONES
        
        async with aiosqlite.connect(self.db_path) as db:
            try:
                db.row_factory = aiosqlite.Row
                
                # Получаем текущее состояние
                async with db.execute(
                    "SELECT drones_hired FROM users WHERE user_id = ?",
                    (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                
                if not row:
                    return {"success": False, "error": "Пользователь не найден"}
                
                drones_hired = row['drones_hired'] or 0
                free_slots = MAX_HIRED_DRONES - drones_hired
                
                if free_slots <= 0:
                    return {"success": False, "error": f"Достигнут лимит найма ({MAX_HIRED_DRONES}/{MAX_HIRED_DRONES})"}
                
                # Получаем количество дронов
                key = f"{drone_type}_lvl{level}"
                async with db.execute(
                    f"SELECT {key} FROM user_drones WHERE user_id = ?",
                    (user_id,)
                ) as cursor:
                    drones_row = await cursor.fetchone()
                
                available = drones_row[key] if drones_row else 0
                
                can_hire = min(count, available, free_slots)
                
                if can_hire == 0:
                    return {"success": False, "error": "Недостаточно свободных дронов"}
                
                # Обновляем
                await db.execute(
                    f"UPDATE user_drones SET {key} = {key} - ? WHERE user_id = ?",
                    (can_hire, user_id)
                )
                
                await db.execute(
                    "UPDATE users SET drones_hired = drones_hired + ? WHERE user_id = ?",
                    (can_hire, user_id)
                )
                
                await db.commit()
                
                return {
                    "success": True,
                    "count": can_hire,
                    "new_hired": drones_hired + can_hire
                }
            except Exception as e:
                print(f"Error hiring drone: {e}")
                return {"success": False, "error": str(e)}

    async def upgrade_drone(self, user_id: int, drone_type: str, current_level: int, count: int = 1) -> Dict:
        """
        Улучшить дронов по правилу 5->1.
        
        Returns:
            Dict с ключами: success, error, count
        """
        from game.drones import MAX_DRONE_LEVEL
        
        if current_level >= MAX_DRONE_LEVEL:
            return {"success": False, "error": "Достигнут максимальный уровень"}
        
        async with aiosqlite.connect(self.db_path) as db:
            try:
                db.row_factory = aiosqlite.Row
                
                key_current = f"{drone_type}_lvl{current_level}"
                key_next = f"{drone_type}_lvl{current_level + 1}"
                
                # Получаем количество дронов
                async with db.execute(
                    f"SELECT {key_current} FROM user_drones WHERE user_id = ?",
                    (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                
                available = row[key_current] if row else 0
                needed = 5 * count
                
                if available < needed:
                    max_upgrades = available // 5
                    if max_upgrades == 0:
                        return {"success": False, "error": f"Недостаточно свободных дронов для улучшения. Доступно: {available}"}
                    count = max_upgrades
                    needed = 5 * count
                
                # Обновляем
                await db.execute(
                    f"UPDATE user_drones SET {key_current} = {key_current} - ?, {key_next} = {key_next} + ? WHERE user_id = ?",
                    (needed, count, user_id)
                )
                
                await db.commit()
                
                return {
                    "success": True,
                    "count": count,
                    "drones_used": needed
                }
            except Exception as e:
                print(f"Error upgrading drone: {e}")
                return {"success": False, "error": str(e)}

    async def sell_drone(self, user_id: int, drone_type: str, level: int, count: int = 1) -> Dict:
        """
        Продать дронов за 30% от стоимости.
        
        Returns:
            Dict с ключами: success, error, count, reward
        """
        from game.drones import DroneSystem
        
        async with aiosqlite.connect(self.db_path) as db:
            try:
                db.row_factory = aiosqlite.Row
                
                key = f"{drone_type}_lvl{level}"
                
                # Получаем количество дронов
                async with db.execute(
                    f"SELECT {key} FROM user_drones WHERE user_id = ?",
                    (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                
                available = row[key] if row else 0
                
                can_sell = min(count, available)
                
                if can_sell == 0:
                    return {"success": False, "error": "Недостаточно дронов для продажи"}
                
                # Рассчитываем награду
                sell_price = DroneSystem.get_sell_price(drone_type, level)
                reward = {
                    'metal': sell_price['metal'] * can_sell,
                    'crystals': sell_price['crystals'] * can_sell,
                    'dark_matter': sell_price['dark_matter'] * can_sell
                }
                
                # Обновляем
                await db.execute(
                    f"UPDATE user_drones SET {key} = {key} - ? WHERE user_id = ?",
                    (can_sell, user_id)
                )
                
                await db.execute(
                    """UPDATE users SET 
                       metal = metal + ?,
                       crystals = crystals + ?,
                       dark_matter = dark_matter + ?
                       WHERE user_id = ?""",
                    (reward['metal'], reward['crystals'], reward['dark_matter'], user_id)
                )
                
                await db.commit()
                
                return {
                    "success": True,
                    "count": can_sell,
                    "reward": reward
                }
            except Exception as e:
                print(f"Error selling drone: {e}")
                return {"success": False, "error": str(e)}

    async def send_drones_to_mission(self, user_id: int) -> Dict:
        """
        Отправить всех свободных дронов на миссию (2 часа).
        
        Returns:
            Dict с ключами: success, error, drones_sent, hired_until
        """
        from datetime import datetime, timedelta
        from game.drones import MISSION_DURATION_MINUTES
        
        async with aiosqlite.connect(self.db_path) as db:
            try:
                db.row_factory = aiosqlite.Row
                
                # Получаем текущее состояние
                async with db.execute(
                    """SELECT u.drones_hired, u.hired_until, u.storage_metal, u.storage_crystal, u.storage_dark,
                              ud.base_lvl1, ud.base_lvl2, ud.base_lvl3, ud.base_lvl4, ud.base_lvl5,
                              ud.miner_lvl1, ud.miner_lvl2, ud.miner_lvl3, ud.miner_lvl4, ud.miner_lvl5,
                              ud.laser_lvl1, ud.laser_lvl2, ud.laser_lvl3, ud.laser_lvl4, ud.laser_lvl5,
                              ud.quantum_lvl1, ud.quantum_lvl2, ud.quantum_lvl3, ud.quantum_lvl4, ud.quantum_lvl5,
                              ud.ai_lvl1, ud.ai_lvl2, ud.ai_lvl3, ud.ai_lvl4, ud.ai_lvl5
                       FROM users u
                       LEFT JOIN user_drones ud ON u.user_id = ud.user_id
                       WHERE u.user_id = ?""",
                    (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                
                if not row:
                    return {"success": False, "error": "Пользователь не найден"}
                
                # Проверяем, есть ли ресурсы в хранилище
                if row['storage_metal'] > 0 or row['storage_crystal'] > 0 or row['storage_dark'] > 0:
                    return {"success": False, "error": "Сначала соберите ресурсы"}
                
                # Проверяем, не в полёте ли уже
                if row['hired_until']:
                    hired_until = datetime.fromisoformat(row['hired_until'])
                    if datetime.now() < hired_until:
                        return {"success": False, "error": "Дроны уже в полёте"}
                
                # Считаем свободных дронов
                drones_in_angar = 0
                for dtype in ['base', 'miner', 'laser', 'quantum', 'ai']:
                    for lvl in range(1, 6):
                        drones_in_angar += row[f"{dtype}_lvl{lvl}"] or 0
                
                if drones_in_angar == 0:
                    return {"success": False, "error": "Нет свободных дронов"}
                
                # Отправляем
                hired_until = datetime.now() + timedelta(minutes=MISSION_DURATION_MINUTES)
                new_hired = (row['drones_hired'] or 0) + drones_in_angar
                
                await db.execute(
                    """UPDATE users SET 
                       drones_hired = ?,
                       hired_until = ?,
                       last_update = ?
                       WHERE user_id = ?""",
                    (new_hired, hired_until.isoformat(), datetime.now().isoformat(), user_id)
                )
                
                # Обнуляем дронов в ангаре (они теперь в найме)
                await db.execute(
                    """UPDATE user_drones SET 
                       base_lvl1=0, base_lvl2=0, base_lvl3=0, base_lvl4=0, base_lvl5=0,
                       miner_lvl1=0, miner_lvl2=0, miner_lvl3=0, miner_lvl4=0, miner_lvl5=0,
                       laser_lvl1=0, laser_lvl2=0, laser_lvl3=0, laser_lvl4=0, laser_lvl5=0,
                       quantum_lvl1=0, quantum_lvl2=0, quantum_lvl3=0, quantum_lvl4=0, quantum_lvl5=0,
                       ai_lvl1=0, ai_lvl2=0, ai_lvl3=0, ai_lvl4=0, ai_lvl5=0
                       WHERE user_id = ?""",
                    (user_id,)
                )
                
                await db.commit()
                
                return {
                    "success": True,
                    "drones_sent": drones_in_angar,
                    "new_hired": new_hired,
                    "hired_until": hired_until.isoformat()
                }
            except Exception as e:
                print(f"Error sending drones: {e}")
                return {"success": False, "error": str(e)}

    async def update_drone_storage(self, user_id: int) -> Dict:
        """
        Обновить хранилище дронов (добавить накопленный доход).
        
        Returns:
            Dict с накопленным доходом
        """
        from datetime import datetime
        from game.drones import DroneSystem, MAX_HIRED_DRONES
        
        async with aiosqlite.connect(self.db_path) as db:
            try:
                db.row_factory = aiosqlite.Row
                
                # Получаем данные
                async with db.execute(
                    """SELECT drones_hired, hired_until, last_update, 
                              storage_metal, storage_crystal, storage_dark
                       FROM users WHERE user_id = ?""",
                    (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                
                if not row or not row['drones_hired']:
                    return {"metal": 0, "crystals": 0, "dark_matter": 0, "minutes_passed": 0}
                
                # Проверяем статус миссии
                hired_until_str = row['hired_until']
                if hired_until_str:
                    hired_until = datetime.fromisoformat(hired_until_str)
                    now = datetime.now()
                    
                    # Если миссия закончилась, считаем только до момента окончания
                    if now > hired_until:
                        last_update_str = row['last_update']
                        last_update = datetime.fromisoformat(last_update_str) if last_update_str else hired_until
                        
                        # Считаем до hired_until
                        minutes_passed = int((hired_until - last_update).total_seconds() / 60)
                        minutes_passed = max(0, min(minutes_passed, 120))  # Максимум 2 часа
                    else:
                        last_update_str = row['last_update']
                        last_update = datetime.fromisoformat(last_update_str) if last_update_str else now
                        minutes_passed = int((now - last_update).total_seconds() / 60)
                else:
                    return {"metal": 0, "crystals": 0, "dark_matter": 0, "minutes_passed": 0}
                
                if minutes_passed <= 0:
                    return {"metal": 0, "crystals": 0, "dark_matter": 0, "minutes_passed": 0}
                
                # Получаем данные о дронах (для расчёта дохода)
                # Note: в упрощённой версии берём средний доход
                # В полной версии нужно хранить какие дроны в найме
                async with db.execute(
                    """SELECT * FROM user_drones WHERE user_id = ?""",
                    (user_id,)
                ) as cursor:
                    drones_row = await cursor.fetchone()
                
                drones_data = dict(drones_row) if drones_row else {}
                
                # Рассчитываем доход (упрощённо - все дроны работают)
                income_per_minute = DroneSystem.calculate_income_per_minute(drones_data, row['drones_hired'])
                
                accumulated = {
                    'metal': income_per_minute['metal'] * minutes_passed,
                    'crystals': income_per_minute['crystals'] * minutes_passed,
                    'dark_matter': income_per_minute['dark_matter'] * minutes_passed
                }
                
                # Обновляем хранилище
                new_storage = {
                    'metal': (row['storage_metal'] or 0) + accumulated['metal'],
                    'crystals': (row['storage_crystal'] or 0) + accumulated['crystals'],
                    'dark_matter': (row['storage_dark'] or 0) + accumulated['dark_matter']
                }
                
                await db.execute(
                    """UPDATE users SET 
                       storage_metal = ?,
                       storage_crystal = ?,
                       storage_dark = ?,
                       storage_updated = ?,
                       last_update = ?
                       WHERE user_id = ?""",
                    (new_storage['metal'], new_storage['crystal'], new_storage['dark_matter'],
                     datetime.now().isoformat(), datetime.now().isoformat(), user_id)
                )
                
                await db.commit()
                
                return {
                    "metal": accumulated['metal'],
                    "crystals": accumulated['crystals'],
                    "dark_matter": accumulated['dark_matter'],
                    "minutes_passed": minutes_passed,
                    "total_storage": new_storage
                }
            except Exception as e:
                print(f"Error updating storage: {e}")
                return {"metal": 0, "crystals": 0, "dark_matter": 0, "minutes_passed": 0}

    async def collect_drone_storage(self, user_id: int) -> Dict:
        """
        Собрать ресурсы из хранилища дронов.
        
        Returns:
            Dict с ключами: success, error, collected
        """
        from datetime import datetime
        from game.drones import DroneSystem
        
        async with aiosqlite.connect(self.db_path) as db:
            try:
                db.row_factory = aiosqlite.Row
                
                # Сначала обновляем хранилище
                await self.update_drone_storage(user_id)
                
                # Получаем данные
                async with db.execute(
                    """SELECT storage_metal, storage_crystal, storage_dark, 
                              drones_hired, hired_until, has_premium
                       FROM users WHERE user_id = ?""",
                    (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                
                if not row:
                    return {"success": False, "error": "Пользователь не найден"}
                
                collected = {
                    'metal': row['storage_metal'] or 0,
                    'crystals': row['storage_crystal'] or 0,
                    'dark_matter': row['storage_dark'] or 0
                }
                
                if collected['metal'] == 0 and collected['crystals'] == 0 and collected['dark_matter'] == 0:
                    return {"success": False, "error": "Хранилище пусто"}
                
                # Проверяем правило 24 часов
                should_clear = False
                if row['hired_until']:
                    hired_until = datetime.fromisoformat(row['hired_until'])
                    hours_passed = (datetime.now() - hired_until).total_seconds() / 3600
                    
                    if hours_passed >= 24:
                        should_clear = True
                        collected = {'metal': 0, 'crystals': 0, 'dark_matter': 0}
                
                # Добавляем ресурсы на баланс
                if not should_clear:
                    await db.execute(
                        """UPDATE users SET 
                           metal = metal + ?,
                           crystals = crystals + ?,
                           dark_matter = dark_matter + ?
                           WHERE user_id = ?""",
                        (collected['metal'], collected['crystals'], collected['dark_matter'], user_id)
                    )
                
                # Очищаем хранилище
                await db.execute(
                    """UPDATE users SET 
                       storage_metal = 0,
                       storage_crystal = 0,
                       storage_dark = 0,
                       storage_updated = ?
                       WHERE user_id = ?""",
                    (datetime.now().isoformat(), user_id)
                )
                
                # Если миссия закончилась и ресурсы собраны - возвращаем дронов
                if row['hired_until']:
                    hired_until = datetime.fromisoformat(row['hired_until'])
                    if datetime.now() > hired_until:
                        # Возвращаем дронов в ангар (упрощённо - просто сбрасываем hired)
                        # В полной версии нужно вернуть дронов в user_drones
                        await db.execute(
                            """UPDATE users SET 
                               drones_hired = 0,
                               hired_until = NULL
                               WHERE user_id = ?""",
                            (user_id,)
                        )
                
                await db.commit()
                
                return {
                    "success": True,
                    "collected": collected,
                    "was_cleared": should_clear
                }
            except Exception as e:
                print(f"Error collecting storage: {e}")
                return {"success": False, "error": str(e)}

    async def upgrade_all_drones(self, user_id: int) -> Dict:
        """
        Улучшить всех дронов сразу (только для premium).
        
        Returns:
            Dict с результатами улучшения
        """
        from game.drones import DRONE_TYPES
        
        async with aiosqlite.connect(self.db_path) as db:
            try:
                db.row_factory = aiosqlite.Row
                
                # Проверяем премиум
                async with db.execute(
                    "SELECT has_premium FROM users WHERE user_id = ?",
                    (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                
                if not row or not row['has_premium']:
                    return {"success": False, "error": "Требуется привилегия"}
                
                # Получаем дронов
                async with db.execute(
                    "SELECT * FROM user_drones WHERE user_id = ?",
                    (user_id,)
                ) as cursor:
                    drones_row = await cursor.fetchone()
                
                if not drones_row:
                    return {"success": True, "upgraded": 0}
                
                drones_data = dict(drones_row)
                total_upgraded = 0
                
                # Улучшаем каждый тип дронов
                for drone_type in DRONE_TYPES:
                    for level in range(1, 5):  # 1-4 уровни можно улучшать
                        key = f"{drone_type}_lvl{level}"
                        available = drones_data.get(key, 0)
                        
                        while available >= 5:
                            upgrades = available // 5
                            
                            # Обновляем
                            await db.execute(
                                f"""UPDATE user_drones SET 
                                    {key} = {key} - ?,
                                    {drone_type}_lvl{level + 1} = {drone_type}_lvl{level + 1} + ?
                                    WHERE user_id = ?""",
                                (upgrades * 5, upgrades, user_id)
                            )
                            
                            total_upgraded += upgrades
                            available = available % 5
                
                await db.commit()
                
                return {
                    "success": True,
                    "upgraded": total_upgraded
                }
            except Exception as e:
                print(f"Error upgrading all drones: {e}")
                return {"success": False, "error": str(e)}


db_manager = DatabaseManager()
