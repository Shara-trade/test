# Оптимизация производительности

## Обзор

Реализованы три уровня оптимизации:
1. Connection Pool — переиспользование соединений
2. Кэширование запросов — кэш результатов
3. Оптимизированные запросы — один запрос вместо нескольких

---

## Connection Pool

### Использование

```python
from database.pool import get_pool, get_connection

# Через контекстный менеджер
async with get_connection() as conn:
    async with conn.execute("SELECT * FROM users") as cursor:
        rows = await cursor.fetchall()

# Напрямую
pool = get_pool()
conn = await pool.acquire()
try:
    # работаем с conn
    pass
finally:
    await pool.release(conn)
```

### Конфигурация

```python
# В main.py
await init_pool(max_connections=10)
```

### PRAGMA оптимизации

При создании соединения применяются:
- `journal_mode=WAL` — лучшая конкурентность
- `synchronous=NORMAL` — быстрее, безопасно для WAL
- `cache_size=10000` — ~40MB кэш страниц
- `temp_store=MEMORY` — временные данные в памяти

---

## Кэширование запросов

### Топы (5 минут)

```python
from database.query_cache import get_cached_top, set_cached_top

# Получить
cached = await get_cached_top('level', page=1, per_page=10)

# Сохранить
await set_cached_top('level', page=1, data=players, per_page=10)
```

### Ранги пользователей (1 минута)

```python
from database.query_cache import get_cached_user_rank, set_cached_user_rank

rank = await get_cached_user_rank(user_id, 'level')
await set_cached_user_rank(user_id, 'level', rank)
```

### Справочники (1 час)

```python
from database.query_cache import get_cached_items_catalog, set_cached_items_catalog

items = await get_cached_items_catalog()
await set_cached_items_catalog(items)
```

### Инвалидация кэша

```python
from database.query_cache import invalidate_user_cache, invalidate_tops_cache

# Инвалидировать кэш пользователя
await invalidate_user_cache(user_id)

# Инвалидировать все топы
await invalidate_tops_cache()
```

---

## Оптимизированные запросы

### get_user_full_profile

**Было:** 4 отдельных запроса
```python
user = await db.get_user(user_id)
drones = await db.get_drones(user_id)
inventory = await db.get_inventory(user_id)
containers = await db.get_containers_count(user_id)
```

**Стало:** 1 запрос с подзапросами
```python
profile = await db.get_user_full_profile(user_id)
# Содержит все данные: user + drones_count + items_count + containers_count + modules_count
```

### get_user_cached

Кэширование профиля пользователя:

```python
# Кэш на 30 секунд
user = await db.get_user_cached(user_id, ttl=30)

# Инвалидация
await db.invalidate_user_cache(user_id)
```

---

## Сравнение производительности

| Операция | До | После | Улучшение |
|----------|-----|-------|-----------|
| Получение профиля | 4 запроса | 1 запрос | 4x быстрее |
| Создание соединения | Каждое обращение | Переиспользование | ~10x быстрее |
| Топ игроков | Запрос каждый раз | Кэш 5 мин | Мгновенно из кэша |
| Ранг пользователя | Запрос каждый раз | Кэш 1 мин | Мгновенно из кэша |

---

## Рекомендации

### Когда использовать кэш

✅ **Использовать:**
- Топы и рейтинги
- Справочники (предметы, материалы)
- Профили для отображения
- Ранги пользователей

❌ **Не использовать:**
- Операции записи
- Критичные к актуальности данные
- Большие объёмы данных

### TTL по типам данных

| Тип данных | TTL | Причина |
|------------|-----|---------|
| Топы | 5 мин | Не критична точность |
| Ранги | 1 мин | Важно для UX |
| Профили | 30 сек | Баланс актуальности |
| Справочники | 1 час | Редко меняются |
| Бонусы модулей | 10 сек | Частые изменения |

---

## Мониторинг

### Статистика connection pool

```python
from database.pool import get_pool

stats = get_pool().stats
# {
#     "total_connections": 5,
#     "available": 3,
#     "in_use": 2,
#     "max_connections": 10
# }
```

### Очистка истёкшего кэша

```python
from database.query_cache import query_cache

# Удалить истёкшие записи
await query_cache.cleanup_expired()
```

---

## Миграции

Применены миграции:
- `001_add_performance_indexes` — индексы для частых запросов
- `003_optimize_database` — документация PRAGMA настроек

Для применения:
```bash
python -m database.migrate apply
```
