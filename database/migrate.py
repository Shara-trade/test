"""
Утилита для управления миграциями базы данных.

Usage:
    python -m database.migrate status          # Показать статус миграций
    python -m database.migrate apply           # Применить все ожидающие миграции
    python -m database.migrate create <name>   # Создать новую миграцию
    python -m database.migrate rollback <name> # Откатить миграцию
    python -m database.migrate info            # Информация о БД
"""
import asyncio
import sys
import os
import io

# Настройка вывода для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Добавляем корень проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATABASE_PATH
from database.migrations import MigrationManager, create_migration, check_database_version, init_database


async def cmd_status():
    """Показать статус миграций"""
    manager = MigrationManager(DATABASE_PATH)
    
    applied = manager.get_applied_migrations()
    pending = manager.get_pending_migrations()
    
    print("\n📊 Статус миграций:")
    print(f"  Применено: {len(applied)}")
    print(f"  Ожидают: {len(pending)}")
    
    if applied:
        print("\n✅ Применённые миграции:")
        for name in applied:
            print(f"  - {name}")
    
    if pending:
        print("\n⏳ Ожидающие миграции:")
        for name in pending:
            print(f"  - {name}")
    
    if not applied and not pending:
        print("\n  Миграций нет")


async def cmd_apply():
    """Применить все ожидающие миграции"""
    manager = MigrationManager(DATABASE_PATH)
    
    pending = manager.get_pending_migrations()
    if not pending:
        print("✅ Все миграции уже применены")
        return
    
    print(f"\n⏳ Применение {len(pending)} миграций...")
    applied = await manager.apply_all_pending()
    
    print(f"\n✅ Применено: {applied}/{len(pending)}")


async def cmd_rollback(migration_name: str):
    """Откатить миграцию"""
    manager = MigrationManager(DATABASE_PATH)
    
    success = await manager.rollback_migration(migration_name)
    if success:
        print(f"✅ Миграция {migration_name} откачена")
    else:
        print(f"❌ Не удалось откатить {migration_name}")


async def cmd_info():
    """Показать информацию о базе данных"""
    info = await check_database_version(DATABASE_PATH)
    
    print("\n📊 Информация о базе данных:")
    print(f"  Путь: {DATABASE_PATH}")
    print(f"  Существует: {'Да' if info['exists'] else 'Нет'}")
    
    if info['exists']:
        size_kb = info['size'] / 1024
        print(f"  Размер: {size_kb:.1f} KB")
        print(f"  Таблиц: {len(info['tables'])}")
        print(f"  Миграций применено: {info['migrations_applied']}")
        
        print("\n📋 Таблицы:")
        for table in info['tables']:
            print(f"  - {table}")


def cmd_create(name: str):
    """Создать новую миграцию"""
    filepath = create_migration(name)
    print(f"✅ Миграция создана: {filepath}")


async def cmd_init():
    """Инициализировать БД из schema.sql"""
    if os.path.exists(DATABASE_PATH):
        print("⚠️ База данных уже существует!")
        response = input("Пересоздать? (yes/no): ")
        if response.lower() != 'yes':
            print("Отменено")
            return
        
        os.remove(DATABASE_PATH)
        print("🗑 Старая БД удалена")
    
    await init_database(DATABASE_PATH)
    print(f"✅ База данных создана: {DATABASE_PATH}")


def print_help():
    """Показать справку"""
    print(__doc__)


async def main():
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1]
    
    if command == 'status':
        await cmd_status()
    
    elif command == 'apply':
        await cmd_apply()
    
    elif command == 'rollback' and len(sys.argv) > 2:
        await cmd_rollback(sys.argv[2])
    
    elif command == 'create' and len(sys.argv) > 2:
        cmd_create(sys.argv[2])
    
    elif command == 'info':
        await cmd_info()
    
    elif command == 'init':
        await cmd_init()
    
    else:
        print_help()


if __name__ == '__main__':
    asyncio.run(main())
