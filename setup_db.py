# Скрипт для создания database.py с правильными отступами

content = '''"""
Работа с базой данных SQLite
"""
import aiosqlite
from typing import Optional, Dict, Any
from config import DATABASE_PATH


class Database:
 def __init__(self, db_path: str = DATABASE_PATH):
 self.db_path = db_path

 async def init_db(self):
 """Инициализация базы данных и создание таблиц"""
 async with aiosqlite.connect(self.db_path) as db:
 await db.execute("""
 CREATE TABLE IF NOT EXISTS users (
 user_id INTEGER PRIMARY KEY,
 username TEXT,
 first_name TEXT,
 last_name TEXT,
 level INTEGER DEFAULT1,
 experience INTEGER DEFAULT0,
 prestige INTEGER DEFAULT0,
 metal INTEGER DEFAULT0,
 crystals INTEGER DEFAULT0,
 dark_matter INTEGER DEFAULT0,
 energy INTEGER DEFAULT1000,
 max_energy INTEGER DEFAULT1000,
 credits INTEGER DEFAULT0,
 quantum_tokens INTEGER DEFAULT0,
 current_system TEXT DEFAULT 'alpha_7',
 total_clicks INTEGER DEFAULT0,
 total_mined INTEGER DEFAULT0,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 referral_code TEXT UNIQUE,
 referred_by INTEGER DEFAULT NULL,
 is_banned INTEGER DEFAULT0
 )
 """)
 await db.commit()

 async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
 """Получить данные пользователя"""
 async with aiosqlite.connect(self.db_path) as db:
 db.row_factory = aiosqlite.Row
 async with db.execute(
 "SELECT * FROM users WHERE user_id = ?", (user_id,)
 ) as cursor:
 row = await cursor.fetchone()
 return dict(row) if row else None

 async def create_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> bool:
 """Создать нового пользователя"""
 async with aiosqlite.connect(self.db_path) as db:
 try:
 referral_code = f"REFuser_id}"
 await db.execute("""
 INSERT INTO users (user_id, username, first_name, last_name, referral_code)
 VALUES (?, ?, ?, ?, ?)
 """, (user_id, username, first_name, last_name, referral_code))
 await db.commit()
 return True
 except Exception as e:
 print(f"Error creating user: {e}")
 return False

 async def update_user_activity(self, user_id: int):
 """Обновить время последней активности"""
 async with aiosqlite.connect(self.db_path) as db:
 await db.execute(
 "UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE user_id = ?",
 (user_id,)
 )
 await db.commit()

 async def update_user_resources(self, user_id: int, metal: int =0, crystals: int =0, dark_matter: int =0, energy: int = None):
 """Обновить ресурсы пользователя"""
 async with aiosqlite.connect(self.db_path) as db:
 updates = []
 params = []
 
 if metal !=0:
 updates.append("metal = metal + ?")
 params.append(metal)
 if crystals !=0:
 updates.append("crystals = crystals + ?")
 params.append(crystals)
 if dark_matter !=0:
 updates.append("dark_matter = dark_matter + ?")
 params.append(dark_matter)
 if energy is not None:
 updates.append("energy = ?")
 params.append(energy)
 
 if updates:
 query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
 params.append(user_id)
 await db.execute(query, params)
 await db.commit()


# Глобальный экземпляр базы данных
db = Database()
'''

with open('database.py', 'w', encoding='utf-8') as f:
 f.write(content)

print('database.py создан успешно!')
