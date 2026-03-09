"""
Section4: Database Manager
"""
import aiosqlite
from typing import Optional, List
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

    async def get_user(self, user_id: int) -> Optional[User]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    data = dict(row)
                    data["is_banned"] = bool(data.get("is_banned", 0))
                    return User(**data)
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

    async def get_drones(self, user_id: int) -> List[Drone]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM drones WHERE user_id = ?", (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [Drone(**dict(r)) for r in rows]

    async def get_item(self, item_key: str) -> Optional[Item]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM items WHERE item_key = ?", (item_key,)
            ) as cursor:
                row = await cursor.fetchone()
                return Item(**dict(row)) if row else None


db_manager = DatabaseManager()
