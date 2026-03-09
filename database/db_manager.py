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

    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Получить пользователя как словарь"""
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
                    return data
                return None

    async def create_user(self, user_id: int, username: str = None,
                          first_name: str = None, last_name: str = None) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            try:
                ref = f"REF{user_id}"
                await db.execute(
                    "INSERT INTO users (user_id, username, first_name, last_name, referral_code) VALUES (?, ?, ?, ?, ?)",
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
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Получаем текущие данные
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT level, experience FROM users WHERE user_id = ?", (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if not row:
                        return {"success": False}
                    
                    current_level = row["level"]
                    current_exp = row["experience"]
                
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
                
                await db.commit()
                
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
                print(f"Error adding experience: {e}")
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
                    
                    current_heat = row["heat"]
                
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

    async def update_last_activity(self, user_id: int):
        """Обновить время последней активности"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )
            await db.commit()

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


db_manager = DatabaseManager()
