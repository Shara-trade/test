"""
Система миграций базы данных.
Простая альтернатива Alembic для SQLite.
"""
import os
import aiosqlite
import logging
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger("migrations")


class MigrationManager:
    """Менеджер миграций базы данных"""
    
    def __init__(self, db_path: str, migrations_dir: str = "database/migrations"):
        self.db_path = db_path
        self.migrations_dir = migrations_dir
        self._ensure_migrations_table()
    
    def _ensure_migrations_table(self):
        """Создать таблицу миграций если не существует"""
        import sqlite3
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def get_applied_migrations(self) -> List[str]:
        """Получить список применённых миграций"""
        import sqlite3
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT name FROM migrations ORDER BY id")
            return [row[0] for row in cursor.fetchall()]
    
    def get_pending_migrations(self) -> List[str]:
        """Получить список неприменённых миграций"""
        if not os.path.exists(self.migrations_dir):
            os.makedirs(self.migrations_dir, exist_ok=True)
            return []
        
        applied = set(self.get_applied_migrations())
        all_migrations = []
        
        for filename in os.listdir(self.migrations_dir):
            if filename.endswith('.sql'):
                migration_name = filename[:-4]  # Убираем .sql
                if migration_name not in applied:
                    all_migrations.append(migration_name)
        
        return sorted(all_migrations)
    
    async def apply_migration(self, migration_name: str) -> bool:
        """Применить одну миграцию"""
        migration_file = os.path.join(self.migrations_dir, f"{migration_name}.sql")
        
        if not os.path.exists(migration_file):
            logger.error(f"Migration file not found: {migration_file}")
            return False
        
        try:
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql = f.read()
            
            async with aiosqlite.connect(self.db_path) as conn:
                # Выполняем миграцию
                await conn.executescript(sql)
                
                # Записываем в таблицу миграций
                await conn.execute(
                    "INSERT INTO migrations (name) VALUES (?)",
                    (migration_name,)
                )
                await conn.commit()
            
            logger.info(f"Migration applied: {migration_name}")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed {migration_name}: {e}")
            return False
    
    async def apply_all_pending(self) -> int:
        """Применить все ожидающие миграции"""
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("No pending migrations")
            return 0
        
        applied_count = 0
        for migration_name in pending:
            if await self.apply_migration(migration_name):
                applied_count += 1
            else:
                logger.error(f"Migration stopped at {migration_name}")
                break
        
        return applied_count
    
    async def rollback_migration(self, migration_name: str) -> bool:
        """Откатить одну миграцию (если есть rollback файл)"""
        rollback_file = os.path.join(
            self.migrations_dir, 
            "rollback", 
            f"{migration_name}.sql"
        )
        
        if not os.path.exists(rollback_file):
            logger.error(f"Rollback file not found: {rollback_file}")
            return False
        
        try:
            with open(rollback_file, 'r', encoding='utf-8') as f:
                sql = f.read()
            
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.executescript(sql)
                await conn.execute(
                    "DELETE FROM migrations WHERE name = ?",
                    (migration_name,)
                )
                await conn.commit()
            
            logger.info(f"Migration rolled back: {migration_name}")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed {migration_name}: {e}")
            return False


def create_migration(name: str, migrations_dir: str = "database/migrations"):
    """
    Создать файл новой миграции.
    
    Args:
        name: Название миграции (например, "001_add_user_settings")
        migrations_dir: Директория для миграций
    """
    os.makedirs(migrations_dir, exist_ok=True)
    os.makedirs(os.path.join(migrations_dir, "rollback"), exist_ok=True)
    
    # Определяем номер миграции
    existing = [f for f in os.listdir(migrations_dir) if f.endswith('.sql')]
    next_num = len(existing) + 1
    
    filename = f"{next_num:03d}_{name}.sql"
    filepath = os.path.join(migrations_dir, filename)
    
    # Шаблон миграции
    template = f"""-- Migration: {name}
-- Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}

-- Write your migration SQL here:


-- Rollback (copy to rollback/{filename}):
-- DROP TABLE IF EXISTS ...;
"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(template)
    
    print(f"Created migration: {filepath}")
    return filepath


async def init_database(db_path: str, schema_path: str = "database/schema.sql"):
    """
    Инициализировать базу данных из schema.sql.
    Используется при первом запуске.
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    async with aiosqlite.connect(db_path) as conn:
        await conn.executescript(schema_sql)
        await conn.commit()
    
    logger.info(f"Database initialized from {schema_path}")


async def check_database_version(db_path: str) -> dict:
    """
    Проверить версию и состояние базы данных.
    
    Returns:
        dict с информацией о БД
    """
    info = {
        "exists": os.path.exists(db_path),
        "size": 0,
        "migrations_applied": 0,
        "tables": [],
        "pending_migrations": 0
    }
    
    if info["exists"]:
        info["size"] = os.path.getsize(db_path)
        
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            # Получаем список таблиц
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            info["tables"] = [row[0] for row in cursor.fetchall()]
            
            # Получаем количество миграций
            try:
                cursor = conn.execute("SELECT COUNT(*) FROM migrations")
                info["migrations_applied"] = cursor.fetchone()[0]
            except:
                pass
    
    return info
