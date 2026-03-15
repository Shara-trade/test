"""
Утилиты для работы с базой данных
Анализ индексов, статистика, оптимизация
"""
import aiosqlite
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


async def analyze_indexes(db_path: str) -> Dict:
    """
    Анализ использования индексов в БД.
    
    Args:
        db_path: Путь к базе данных
        
    Returns:
        Dict с информацией об индексах
    """
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        
        # Получаем список всех индексов
        async with conn.execute("""
            SELECT 
                name as index_name,
                tbl_name as table_name,
                sql as definition
            FROM sqlite_master
            WHERE type = 'index' AND sql IS NOT NULL
            ORDER BY tbl_name, name
        """) as cursor:
            indexes = await cursor.fetchall()
        
        # Получаем статистику по таблицам
        async with conn.execute("""
            SELECT 
                name as table_name,
                (SELECT COUNT(*) FROM pragma_table_info(m.name)) as column_count
            FROM sqlite_master m
            WHERE type = 'table'
            ORDER BY name
        """) as cursor:
            tables = await cursor.fetchall()
        
        return {
            "indexes": [dict(i) for i in indexes],
            "tables": [dict(t) for t in tables],
            "index_count": len(indexes),
            "table_count": len(tables)
        }


async def get_table_stats(db_path: str, table_name: str) -> Dict:
    """
    Получить статистику по таблице.
    
    Args:
        db_path: Путь к базе данных
        table_name: Имя таблицы
        
    Returns:
        Dict со статистикой
    """
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        
        # Количество записей
        async with conn.execute(f"SELECT COUNT(*) as count FROM {table_name}") as cursor:
            row = await cursor.fetchone()
            count = row["count"] if row else 0
        
        # Размер таблицы (примерный)
        async with conn.execute(f"""
            SELECT 
                SUM(pgsize) as size_bytes
            FROM dbstat
            WHERE name = ?
        """, (table_name,)) as cursor:
            row = await cursor.fetchone()
            size_bytes = row["size_bytes"] if row and row["size_bytes"] else 0
        
        return {
            "table_name": table_name,
            "row_count": count,
            "size_bytes": size_bytes,
            "size_mb": round(size_bytes / 1024 / 1024, 2) if size_bytes else 0
        }


async def get_index_usage(db_path: str) -> List[Dict]:
    """
    Получить информацию об использовании индексов.
    
    Args:
        db_path: Путь к базе данных
        
    Returns:
        List[Dict] с информацией об индексах
    """
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        
        # Получаем информацию об индексах
        async with conn.execute("""
            SELECT 
                m.name as index_name,
                m.tbl_name as table_name,
                GROUP_CONCAT(ii.name, ', ') as columns,
                m.sql as definition
            FROM sqlite_master m
            LEFT JOIN pragma_index_list(m.tbl_name) il ON 1=1
            LEFT JOIN pragma_index_info(il.name) ii ON 1=1
            WHERE m.type = 'index'
            GROUP BY m.name, m.tbl_name, m.sql
            ORDER BY m.tbl_name, m.name
        """) as cursor:
            rows = await cursor.fetchall()
            
            indexes = []
            for row in rows:
                indexes.append({
                    "index_name": row["index_name"],
                    "table_name": row["table_name"],
                    "columns": row["columns"] or "",
                    "definition": row["definition"] or ""
                })
            
            return indexes


async def vacuum_database(db_path: str) -> Dict:
    """
    Оптимизировать базу данных (VACUUM).
    
    Args:
        db_path: Путь к базе данных
        
    Returns:
        Dict с результатом
    """
    import os
    
    size_before = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    
    try:
        async with aiosqlite.connect(db_path) as conn:
            await conn.execute("VACUUM")
            await conn.commit()
        
        size_after = os.path.getsize(db_path)
        
        return {
            "success": True,
            "size_before_mb": round(size_before / 1024 / 1024, 2),
            "size_after_mb": round(size_after / 1024 / 1024, 2),
            "freed_mb": round((size_before - size_after) / 1024 / 1024, 2)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def analyze_query_performance(db_path: str, query: str) -> Dict:
    """
    Проанализировать план выполнения запроса.
    
    Args:
        db_path: Путь к базе данных
        query: SQL запрос
        
    Returns:
        Dict с планом выполнения
    """
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        
        # EXPLAIN QUERY PLAN
        async with conn.execute(f"EXPLAIN QUERY PLAN {query}") as cursor:
            rows = await cursor.fetchall()
            plan = [dict(r) for r in rows]
        
        return {
            "query": query,
            "plan": plan
        }


async def get_database_info(db_path: str) -> Dict:
    """
    Получить общую информацию о базе данных.
    
    Args:
        db_path: Путь к базе данных
        
    Returns:
        Dict с информацией
    """
    import os
    
    if not os.path.exists(db_path):
        return {"exists": False}
    
    size_bytes = os.path.getsize(db_path)
    
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        
        # Список таблиц
        async with conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ) as cursor:
            tables = [r[0] for r in await cursor.fetchall()]
        
        # Список индексов
        async with conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL ORDER BY name"
        ) as cursor:
            indexes = [r[0] for r in await cursor.fetchall()]
        
        # PRAGMA информация
        async with conn.execute("PRAGMA journal_mode") as cursor:
            journal_mode = (await cursor.fetchone())[0]
        
        async with conn.execute("PRAGMA synchronous") as cursor:
            synchronous = (await cursor.fetchone())[0]
        
        async with conn.execute("PRAGMA cache_size") as cursor:
            cache_size = (await cursor.fetchone())[0]
        
        # Количество миграций
        try:
            async with conn.execute("SELECT COUNT(*) FROM migrations") as cursor:
                migrations_count = (await cursor.fetchone())[0]
        except:
            migrations_count = 0
    
    return {
        "exists": True,
        "path": db_path,
        "size_bytes": size_bytes,
        "size_mb": round(size_bytes / 1024 / 1024, 2),
        "tables": tables,
        "tables_count": len(tables),
        "indexes": indexes,
        "indexes_count": len(indexes),
        "journal_mode": journal_mode,
        "synchronous": synchronous,
        "cache_size": cache_size,
        "migrations_count": migrations_count
    }


async def check_foreign_keys(db_path: str) -> List[Dict]:
    """
    Проверить нарушения внешних ключей.
    
    Args:
        db_path: Путь к базе данных
        
    Returns:
        List[Dict] с нарушениями
    """
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        
        # Включаем проверку FK
        await conn.execute("PRAGMA foreign_keys = ON")
        
        # Проверяем нарушения
        async with conn.execute("PRAGMA foreign_key_check") as cursor:
            rows = await cursor.fetchall()
            
            if not rows:
                return []
            
            violations = []
            for row in rows:
                violations.append({
                    "table": row[0],
                    "rowid": row[1],
                    "parent": row[2],
                    "fk_index": row[3]
                })
            
            return violations


async def get_admin_logs_stats(db_path: str) -> Dict:
    """
    Получить статистику по логам админки.
    
    Args:
        db_path: Путь к базе данных
        
    Returns:
        Dict со статистикой
    """
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        
        # Общее количество
        async with conn.execute("SELECT COUNT(*) as count FROM admin_logs") as cursor:
            total = (await cursor.fetchone())["count"]
        
        # По действиям
        async with conn.execute("""
            SELECT action, COUNT(*) as count 
            FROM admin_logs 
            GROUP BY action 
            ORDER BY count DESC
        """) as cursor:
            by_action = [dict(r) for r in await cursor.fetchall()]
        
        # По админам
        async with conn.execute("""
            SELECT admin_id, COUNT(*) as count 
            FROM admin_logs 
            GROUP BY admin_id 
            ORDER BY count DESC
            LIMIT 10
        """) as cursor:
            by_admin = [dict(r) for r in await cursor.fetchall()]
        
        # За последние 24 часа
        async with conn.execute("""
            SELECT COUNT(*) as count 
            FROM admin_logs 
            WHERE datetime(created_at) > datetime('now', '-1 day')
        """) as cursor:
            last_24h = (await cursor.fetchone())["count"]
        
        # За последние 7 дней
        async with conn.execute("""
            SELECT COUNT(*) as count 
            FROM admin_logs 
            WHERE datetime(created_at) > datetime('now', '-7 days')
        """) as cursor:
            last_7d = (await cursor.fetchone())["count"]
        
        return {
            "total": total,
            "by_action": by_action,
            "by_admin": by_admin,
            "last_24h": last_24h,
            "last_7d": last_7d
        }


# Экспорт функций
__all__ = [
    "analyze_indexes",
    "get_table_stats",
    "get_index_usage",
    "vacuum_database",
    "analyze_query_performance",
    "get_database_info",
    "check_foreign_keys",
    "get_admin_logs_stats"
]
