"""
Section4: Database Manager
"""
import aiosqlite
from typing import Optional, List, Dict
from datetime import datetime
from config import DATABASE_PATH
from .models import User, Drone, Item


class DatabaseManager:
    def __init__(self, db_path: str = DATABASE_PATH):
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
        """Опыт, необходимый для достижения уровня"""
        # Формула: 1000 * (1.2 ^ (level - 1))
        return int(1000 * (1.2 ** (level - 1)))

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

    async def add_inventory_item(self, user_id: int, item_key: str, quantity: int = 1) -> Dict:
        """
        Добавить предмет в инвентарь.
        
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

    async def add_item(self, user_id: int, item_key: str, quantity: int = 1) -> Dict:
        """
        Добавить предмет в инвентарь (алиас для add_inventory_item).
        
        Returns:
            Dict с ключами: success, error, item_key, quantity
        """
        result = await self.add_inventory_item(user_id, item_key, quantity)
        return result

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

    # ==================== МОДУЛИ ====================

    async def get_installed_modules(self, user_id: int, target: str = 'player') -> List[Dict]:
        """Получить установленные модули"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            if target == 'player':
                query = "installed_in = 'player'"
                params = (user_id,)
            else:
                query = "installed_in = ?"
                params = (user_id, target)
            
            sql = """SELECT 
                    um.id,
                    um.item_key,
                    um.installed_in,
                    um.slot_number,
                    um.installed_at,
                    COALESCE(it.name, um.item_key) as name,
                    COALESCE(it.description, '') as description,
                    COALESCE(it.rarity, 'common') as rarity,
                    COALESCE(it.icon, '⚙️') as icon,
                    COALESCE(it.effects, '{}') as effects,
                    COALESCE(it.level_required, 1) as level_required
                   FROM user_modules um
                   LEFT JOIN items it ON um.item_key = it.item_key
                   WHERE um.user_id = ? AND """ + query + """
                   ORDER BY um.slot_number"""
            
            async with db.execute(sql, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_available_modules(self, user_id: int) -> List[Dict]:
        """Получить модули в инвентаре (не установленные)"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Модули из инвентаря, которые не установлены
            async with db.execute(
                """SELECT 
                    i.item_id,
                    i.item_key,
                    i.quantity,
                    COALESCE(it.name, i.item_key) as name,
                    COALESCE(it.description, '') as description,
                    COALESCE(it.rarity, 'common') as rarity,
                    COALESCE(it.icon, '⚙️') as icon,
                    COALESCE(it.effects, '{}') as effects,
                    COALESCE(it.level_required, 1) as level_required,
                    COALESCE(it.base_price, 0) as base_price
                   FROM inventory i
                   LEFT JOIN items it ON i.item_key = it.item_key
                   LEFT JOIN user_modules um ON i.item_key = um.item_key AND um.user_id = i.user_id
                   WHERE i.user_id = ? 
                   AND it.item_type = 'module'
                   AND um.id IS NULL
                   AND i.quantity > 0
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

    async def install_module(self, user_id: int, item_key: str, target: str = 'player', slot: int = 1) -> Dict:
        """
        Установить модуль.
        
        Returns:
            Dict с ключами: success, error, item_key, installed_in, slot
        """
        import logging
        logger = logging.getLogger("database")
        
        logger.info(f"[install_module] Attempting to install '{item_key}' for user {user_id}, target={target}, slot={slot}")
        
        async with aiosqlite.connect(self.db_path) as db:
            try:
                db.row_factory = aiosqlite.Row
                
                # Шаг 1: Проверяем наличие модуля в инвентаре
                logger.debug(f"[install_module] Step 1: Checking inventory for user {user_id}, item '{item_key}'")
                async with db.execute(
                    "SELECT item_id, quantity FROM inventory WHERE user_id = ? AND item_key = ?",
                    (user_id, item_key)
                ) as cursor:
                    row = await cursor.fetchone()
                
                if not row:
                    logger.error(f"[install_module] FAILED: Item '{item_key}' not found in inventory for user {user_id}")
                    
                    # Дополнительная диагностика - покажем что есть в инвентаре
                    async with db.execute(
                        "SELECT item_key, quantity FROM inventory WHERE user_id = ?",
                        (user_id,)
                    ) as cursor:
                        all_items = await cursor.fetchall()
                    
                    logger.error(f"[install_module] User {user_id} inventory has {len(all_items)} items: {[dict(i) for i in all_items]}")
                    
                    return {
                        "success": False,
                        "error": "Module not in inventory",
                        "item_key": item_key,
                        "user_id": user_id,
                        "inventory_count": len(all_items)
                    }
                
                current_quantity = row["quantity"]
                logger.debug(f"[install_module] Found in inventory: item_id={row['item_id']}, quantity={current_quantity}")
                
                if current_quantity <= 0:
                    logger.error(f"[install_module] FAILED: Item '{item_key}' has quantity={current_quantity}")
                    return {
                        "success": False,
                        "error": "Module quantity is 0",
                        "item_key": item_key,
                        "quantity": current_quantity
                    }
                
                # Шаг 2: Проверяем, не установлен ли уже
                logger.debug(f"[install_module] Step 2: Checking if already installed")
                async with db.execute(
                    "SELECT id, installed_in FROM user_modules WHERE user_id = ? AND item_key = ?",
                    (user_id, item_key)
                ) as cursor:
                    installed = await cursor.fetchone()
                
                if installed:
                    logger.error(f"[install_module] FAILED: Module '{item_key}' already installed in '{installed['installed_in']}'")
                    return {
                        "success": False,
                        "error": "Module already installed",
                        "item_key": item_key,
                        "installed_in": installed["installed_in"]
                    }
                
                # Шаг 3: Проверяем, занят ли слот
                logger.debug(f"[install_module] Step 3: Checking if slot {slot} is free")
                async with db.execute(
                    "SELECT id, item_key FROM user_modules WHERE user_id = ? AND installed_in = ? AND slot_number = ?",
                    (user_id, target, slot)
                ) as cursor:
                    slot_occupied = await cursor.fetchone()
                
                if slot_occupied:
                    logger.error(f"[install_module] FAILED: Slot {slot} already occupied by '{slot_occupied['item_key']}'")
                    return {
                        "success": False,
                        "error": "Slot already occupied",
                        "slot": slot,
                        "occupied_by": slot_occupied["item_key"]
                    }
                
                # Шаг 4: Устанавливаем модуль
                logger.debug(f"[install_module] Step 4: Installing module")
                await db.execute(
                    "INSERT INTO user_modules (user_id, item_key, installed_in, slot_number) VALUES (?, ?, ?, ?)",
                    (user_id, item_key, target, slot)
                )
                
                # Шаг 5: Уменьшаем количество в инвентаре
                logger.debug(f"[install_module] Step 5: Decreasing inventory quantity")
                new_quantity = current_quantity - 1
                if new_quantity <= 0:
                    await db.execute(
                        "DELETE FROM inventory WHERE item_id = ?",
                        (row["item_id"],)
                    )
                    logger.info(f"[install_module] Removed item from inventory (quantity was 1)")
                else:
                    await db.execute(
                        "UPDATE inventory SET quantity = ? WHERE item_id = ?",
                        (new_quantity, row["item_id"])
                    )
                    logger.info(f"[install_module] Decreased inventory: {current_quantity} -> {new_quantity}")
                
                await db.commit()
                
                logger.info(f"[install_module] SUCCESS: Module '{item_key}' installed for user {user_id} in {target} slot {slot}")
                
                return {
                    "success": True,
                    "item_key": item_key,
                    "installed_in": target,
                    "slot": slot,
                    "remaining_quantity": new_quantity if new_quantity > 0 else 0
                }
                
            except Exception as e:
                logger.error(f"[install_module] EXCEPTION: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return {
                    "success": False,
                    "error": str(e),
                    "item_key": item_key,
                    "user_id": user_id
                }
                
    async def uninstall_module(self, user_id: int, item_key: str) -> Dict:
        """
        Снять модуль и вернуть в инвентарь.
        
        Returns:
            Dict с ключами: success, error, item_key, was_installed_in
        """
        import logging
        logger = logging.getLogger("database")
        
        logger.info(f"[uninstall_module] Attempting to uninstall '{item_key}' for user {user_id}")
        
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Получаем информацию о модуле
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM user_modules WHERE user_id = ? AND item_key = ?",
                    (user_id, item_key)
                ) as cursor:
                    row = await cursor.fetchone()
                
                if not row:
                    logger.error(f"[uninstall_module] FAILED: Module '{item_key}' not installed for user {user_id}")
                    return {
                        "success": False,
                        "error": "Module not installed",
                        "item_key": item_key
                    }
                
                # Удаляем запись
                await db.execute(
                    "DELETE FROM user_modules WHERE user_id = ? AND item_key = ?",
                    (user_id, item_key)
                )
                
                await db.commit()
                
                # Возвращаем в инвентарь
                add_result = await self.add_item(user_id, item_key, 1)
                
                if not add_result.get("success"):
                    logger.error(f"[uninstall_module] Failed to return item to inventory: {add_result}")
                    return {
                        "success": False,
                        "error": f"Failed to return to inventory: {add_result.get('error')}",
                        "item_key": item_key
                    }
                
                logger.info(f"[uninstall_module] SUCCESS: Module '{item_key}' uninstalled and returned to inventory")
                
                return {
                    "success": True,
                    "item_key": item_key,
                    "was_installed_in": row["installed_in"]
                }
                
            except Exception as e:
                logger.error(f"[uninstall_module] EXCEPTION: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return {
                    "success": False,
                    "error": str(e),
                    "item_key": item_key
                }

    async def get_module_bonuses(self, user_id: int, target: str = None) -> Dict:
        """Получить общие бонусы от модулей"""
        import json
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            if target:
                sql = """SELECT effects 
                   FROM user_modules um
                   LEFT JOIN items it ON um.item_key = it.item_key
                   WHERE um.user_id = ? AND installed_in = ?"""
                params = (user_id, target)
            else:
                sql = """SELECT effects 
                   FROM user_modules um
                   LEFT JOIN items it ON um.item_key = it.item_key
                   WHERE um.user_id = ?"""
                params = (user_id,)
            
            async with db.execute(sql, params) as cursor:
                rows = await cursor.fetchall()
            
            # Суммируем бонусы
            total_bonuses = {}
            
            for row in rows:
                effects = row["effects"] or '{}'
                try:
                    effects_dict = json.loads(effects) if isinstance(effects, str) else effects
                    
                    for key, value in effects_dict.items():
                        if key in total_bonuses:
                            total_bonuses[key] += value
                        else:
                            total_bonuses[key] = value
                except:
                    pass
            
            return total_bonuses

    async def get_module_slots_info(self, user_id: int) -> Dict:
        """Получить информацию о слотах модулей"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Получаем уровень игрока
            async with db.execute(
                "SELECT level FROM users WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                level = row["level"] if row else 1
            
            # Базовые слоты: 3, +1 за каждые 10 уровней, максимум 10
            base_slots = 3
            bonus_slots = min(7, level // 10)
            max_player_slots = base_slots + bonus_slots
            
            # Установленные модули на игроке
            async with db.execute(
                "SELECT COUNT(*) as count FROM user_modules WHERE user_id = ? AND installed_in = 'player'",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                installed_player = row["count"] if row else 0
            
            # Модули на дронах
            async with db.execute(
                """SELECT d.drone_id, d.drone_type, d.module_slots,
                          (SELECT COUNT(*) FROM user_modules WHERE installed_in = CAST(d.drone_id AS TEXT)) as installed
                   FROM drones d WHERE d.user_id = ? AND d.is_active = 1""",
                (user_id,)
            ) as cursor:
                drone_rows = await cursor.fetchall()
                drones_info = [dict(r) for r in drone_rows]
            
            return {
                "level": level,
                "player_slots": {
                    "max": max_player_slots,
                    "installed": installed_player,
                    "available": max_player_slots - installed_player
                },
                "drones": drones_info
            }


db_manager = DatabaseManager()
