"""
Применение миграции 004_admin_panel_optimization
Пункт 6 ТЗ - Оптимизация базы данных
"""
import asyncio
import aiosqlite
import os
import sys

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATABASE_PATH


async def apply_migration():
    """Применить миграцию оптимизации админ-панели"""
    
    migration_file = "database/migrations/004_admin_panel_optimization.sql"
    
    if not os.path.exists(migration_file):
        print(f"❌ Файл миграции не найден: {migration_file}")
        return False
    
    print(f"📦 Применение миграции: {migration_file}")
    print(f"📊 База данных: {DATABASE_PATH}")
    print()
    
    # Проверяем, применена ли миграция
    async with aiosqlite.connect(DATABASE_PATH) as conn:
        try:
            async with conn.execute(
                "SELECT 1 FROM migrations WHERE name = '004_admin_panel_optimization'"
            ) as cursor:
                if await cursor.fetchone():
                    print("✅ Миграция уже применена")
                    return True
        except:
            pass
    
    # Читаем SQL
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    # Применяем
    try:
        async with aiosqlite.connect(DATABASE_PATH) as conn:
            # Выполняем миграцию
            await conn.executescript(sql)
            
            # Записываем в таблицу миграций
            await conn.execute(
                "INSERT INTO migrations (name) VALUES (?)",
                ("004_admin_panel_optimization",)
            )
            await conn.commit()
        
        print("✅ Миграция успешно применена!")
        print()
        
        # Показываем статистику
        await show_stats()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка применения миграции: {e}")
        import traceback
        traceback.print_exc()
        return False


async def show_stats():
    """Показать статистику индексов"""
    from database.db_utils import get_database_info, get_index_usage
    
    print("📊 Статистика базы данных:")
    print()
    
    # Общая информация
    info = await get_database_info(DATABASE_PATH)
    
    print(f"  Размер: {info['size_mb']} MB")
    print(f"  Таблиц: {info['tables_count']}")
    print(f"  Индексов: {info['indexes_count']}")
    print(f"  Миграций: {info['migrations_count']}")
    print(f"  Journal mode: {info['journal_mode']}")
    print()
    
    # Индексы
    indexes = await get_index_usage(DATABASE_PATH)
    
    print("📋 Созданные индексы:")
    
    admin_indexes = [i for i in indexes if 'admin' in i['table_name'] or 'admin' in i['index_name']]
    
    for idx in admin_indexes:
        print(f"  • {idx['index_name']} on {idx['table_name']}")
        if idx['columns']:
            print(f"    Columns: {idx['columns']}")
    
    print()
    print(f"  Всего индексов: {len(indexes)}")
    print(f"  Индексов админки: {len(admin_indexes)}")


async def verify_indexes():
    """Проверить, что все нужные индексы созданы"""
    
    required_indexes = [
        "idx_users_username_lower",
        "idx_users_last_activity",
        "idx_admin_logs_admin",
        "idx_admin_logs_action",
        "idx_admin_logs_target",
        "idx_admin_logs_date",
        "idx_bans_user_status",
        "idx_admins_user_active"
    ]
    
    async with aiosqlite.connect(DATABASE_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        
        async with conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"
        ) as cursor:
            existing = [r[0] for r in await cursor.fetchall()]
    
    print("🔍 Проверка индексов:")
    
    all_ok = True
    for idx_name in required_indexes:
        if idx_name in existing:
            print(f"  ✅ {idx_name}")
        else:
            print(f"  ❌ {idx_name} - ОТСУТСТВУЕТ")
            all_ok = False
    
    print()
    
    if all_ok:
        print("✅ Все необходимые индексы созданы")
    else:
        print("⚠️ Некоторые индексы отсутствуют")
    
    return all_ok


async def main():
    """Главная функция"""
    
    print("=" * 60)
    print("ПУНКТ 6 ТЗ - ОПТИМИЗАЦИЯ БАЗЫ ДАННЫХ")
    print("=" * 60)
    print()
    
    # Применяем миграцию
    success = await apply_migration()
    
    if success:
        print()
        print("=" * 60)
        
        # Проверяем индексы
        await verify_indexes()
        
        print()
        print("=" * 60)
        print("✅ ПУНКТ 6 ЗАВЕРШЁН УСПЕШНО")
        print("=" * 60)
    else:
        print()
        print("=" * 60)
        print("❌ ОШИБКА ПРИМЕНЕНИЯ МИГРАЦИИ")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
