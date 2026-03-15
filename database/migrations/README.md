# Миграции базы данных

## Структура

```
database/
├── schema.sql              # Полная схема БД (для инициализации)
├── migrations.py           # Система миграций
├── migrate.py              # CLI утилита
└── migrations/
    ├── 001_add_indexes.sql # Миграция 1
    ├── 002_...             # Миграция 2
    └── rollback/           # Файлы отката
        ├── 001_add_indexes.sql
        └── ...
```

## Команды

### Показать статус миграций
```bash
python -m database.migrate status
```

### Применить все ожидающие миграции
```bash
python -m database.migrate apply
```

### Создать новую миграцию
```bash
python -m database.migrate create add_user_settings
# Создаст файл: migrations/002_add_user_settings.sql
```

### Откатить миграцию
```bash
python -m database.migrate rollback 001_add_indexes
```

### Информация о БД
```bash
python -m database.migrate info
```

### Инициализировать БД заново
```bash
python -m database.migrate init
```

## Автоматическое применение

Миграции автоматически применяются при запуске бота (`main.py`).

## Создание миграции

1. Создайте файл миграции:
   ```bash
   python -m database.migrate create my_migration_name
   ```

2. Отредактируйте файл `migrations/NNN_my_migration_name.sql`:
   ```sql
   -- Migration: my_migration_name
   -- Created: 2025-01-14
   
   ALTER TABLE users ADD COLUMN new_field TEXT DEFAULT '';
   ```

3. Создайте файл отката `migrations/rollback/NNN_my_migration_name.sql`:
   ```sql
   -- Rollback for: my_migration_name
   -- SQLite не поддерживает DROP COLUMN, поэтому создаём новую таблицу
   CREATE TABLE users_backup AS SELECT * FROM users;
   DROP TABLE users;
   -- Пересоздаём таблицу без нового поля...
   ```

## Примечания

- SQLite имеет ограничения на ALTER TABLE
- Для сложных изменений используйте пересоздание таблиц
- Всегда создавайте rollback файлы
- Миграции применяются в порядке имён файлов
