# Улучшение функционала админ-панели (Пункт 4 ТЗ)

## Обзор

Реализованы улучшения функционала:

1. **Расширенный поиск игроков** — с фильтрами по уровню, ресурсам, активности
2. **История изменений игрока** — логирование всех действий над игроком
3. **Шаблоны действий (пресеты)** — 6 готовых наборов для быстрой выдачи
4. **Статистика в реальном времени** — онлайн, активность, добыча
5. **Массовые операции** — выдача ресурсов/предметов множеству игроков

---

## 1. Расширенный поиск игроков

### Использование

```python
from admin import get_admin_service

service = get_admin_service(DATABASE_PATH)

# Простой поиск
result = await service.search_players("username")

# Расширенный поиск с фильтрами
result = await service.search_players_advanced(
    query="player123",           # Поиск по username/ID
    min_level=10,                # Минимальный уровень
    max_level=50,                # Максимальный уровень
    is_banned=False,             # Только незабаненные
    is_admin=False,              # Только не админы
    min_metal=10000,             # Минимум металла
    min_crystals=100,            # Минимум кристаллов
    registered_after="2024-01-01",  # Зарегистрированы после
    last_activity_after="2024-12-01",  # Активны после
    limit=20,
    page=1
)

# Результат
{
    "success": True,
    "players": [...],  # Список игроков
    "total": 150,      # Всего найдено
    "page": 1,
    "has_more": True
}
```

### Доступные фильтры

| Фильтр | Тип | Описание |
|--------|-----|----------|
| `query` | str | Поиск по ID, username, first_name, last_name |
| `min_level` | int | Минимальный уровень |
| `max_level` | int | Максимальный уровень |
| `is_banned` | bool | Фильтр по бану |
| `is_admin` | bool | Фильтр по админке |
| `min_metal` | int | Минимум металла |
| `min_crystals` | int | Минимум кристаллов |
| `registered_after` | str | Дата регистрации (YYYY-MM-DD) |
| `registered_before` | str | Дата регистрации (YYYY-MM-DD) |
| `last_activity_after` | str | Последняя активность (YYYY-MM-DD) |

---

## 2. История изменений игрока

### Использование

```python
# Получить историю
history = await service.get_player_history(
    user_id=123,
    limit=20,
    page=1
)

# Результат
{
    "success": True,
    "user_id": 123,
    "events": [
        {
            "created_at": "2024-12-20 15:30:00",
            "action": "give_container",
            "details": "container_rare x5",
            "admin_name": "admin_user"
        },
        ...
    ],
    "page": 1,
    "has_more": False
}
```

### Форматирование

```python
from admin import format_player_history

# Форматировать историю для вывода
text = format_player_history(history["events"], user_id=123)
```

### Типы действий

| Действие | Эмодзи | Описание |
|----------|--------|----------|
| `edit_resource` | ✏️ | Изменение ресурсов |
| `give_item` | 📦 | Выдача предмета |
| `give_container` | 📦 | Выдача контейнера |
| `give_module` | 🧩 | Выдача модуля |
| `ban_player` | 🚫 | Бан игрока |
| `unban_player` | ✅ | Разбан игрока |
| `apply_preset` | 🎁 | Применение пресета |
| `mass_operation` | 👥 | Массовая операция |

---

## 3. Шаблоны действий (пресеты)

### Доступные пресеты

| ID | Название | Описание |
|----|----------|----------|
| `starter_pack` | 🎁 Стартовый набор | Базовый набор для нового игрока |
| `event_reward` | 🎉 Награда за ивент | Награда за участие в событии |
| `compensation` | ⚖️ Компенсация | Компенсация за баги/проблемы |
| `premium_gift` | ⭐ Премиум подарок | Особый подарок от администрации |
| `weekly_bonus` | 📅 Еженедельный бонус | Бонус за активность |
| `test_reward` | 🧪 Тестовая награда | Для тестирования функций |

### Состав пресетов

#### starter_pack
- **Предметы:** container_common x3, container_rare x1
- **Ресурсы:** металл 5000, кристаллы 100

#### event_reward
- **Предметы:** container_epic x2, container_legendary x1
- **Ресурсы:** металл 50000, кристаллы 5000, тёмная материя 50

#### compensation
- **Предметы:** container_rare x5, container_epic x2
- **Ресурсы:** металл 25000, кристаллы 2500, тёмная материя 25

#### premium_gift
- **Предметы:** container_mythic x1, container_epic x3, container_rare x5
- **Ресурсы:** металл 100000, кристаллы 10000, тёмная материя 100

### Использование

```python
# Получить список пресетов
presets = service.get_presets_list()

# Получить конкретный пресет
preset = service.get_preset("starter_pack")

# Применить пресет к игроку
result = await service.apply_preset(
    preset_id="starter_pack",
    user_id=123,
    admin_id=456
)

# Результат
{
    "success": True,
    "preset_id": "starter_pack",
    "preset_name": "🎁 Стартовый набор",
    "results": {
        "items": [
            {"item_key": "container_common", "quantity": 3},
            {"item_key": "container_rare", "quantity": 1}
        ],
        "resources": {"metal": 5000, "crystals": 100},
        "errors": []
    }
}
```

### Форматирование

```python
from admin import format_preset, format_presets_list

# Описание одного пресета
text = format_preset(preset)

# Список всех пресетов
text = format_presets_list(presets)
```

---

## 4. Статистика в реальном времени

### Основная статистика

```python
# Получить статистику
stats = await service.get_stats()

# Результат
{
    "total_players": 10000,
    "active_today": 1500,
    "online_now": 50,
    "banned_players": 25,
    "new_players_today": 100,
    "new_players_week": 700,
    "total_metal": 50000000,
    "total_crystals": 500000,
    "total_credits": 1000000
}
```

### Статистика в реальном времени

```python
# Получить метрики в реальном времени
realtime = await service.get_realtime_stats()

# Результат
{
    "online_now": 50,              # Онлайн сейчас (5 минут)
    "active_hour": 200,            # Активных за час
    "active_day": 1500,            # Активных за день
    "mined_hour": 100000,          # Добыто за час
    "mined_day": 2000000,          # Добыто за день
    "containers_opened_hour": 50,  # Открыто контейнеров за час
    "clicks_hour": 50000,          # Кликов за час
    "timestamp": "2024-12-20T15:30:00"
}
```

### Статистика активности по дням

```python
# Получить статистику за 7 дней
activity = await service.get_activity_stats(days=7)

# Результат
{
    "daily_activity": [
        {"date": "2024-12-20", "active_users": 1500, "total_mined": 2000000},
        {"date": "2024-12-19", "active_users": 1400, "total_mined": 1800000},
        ...
    ],
    "daily_registrations": [
        {"date": "2024-12-20", "new_users": 100},
        {"date": "2024-12-19", "new_users": 90},
        ...
    ],
    "period_days": 7
}
```

### Форматирование

```python
from admin import format_admin_stats, format_realtime_stats

# Основная статистика
text = format_admin_stats(stats)

# Статистика в реальном времени
text = format_realtime_stats(realtime)
```

---

## 5. Массовые операции

### Подготовка операции

```python
# Получить список пользователей по критериям
prep = await service.prepare_mass_operation(
    min_level=10,           # Уровень от 10
    max_level=50,           # Уровень до 50
    active_last_days=7,     # Активны последние 7 дней
    include_banned=False    # Не включать забаненных
)

# Результат
{
    "success": True,
    "total_users": 500,
    "user_ids": [1, 2, 3, ...],  # Первые 100 для предпросмотра
    "filters": {...}
}
```

### Массовая выдача предмета

```python
# Выдать предмет множеству игроков
result = await service.mass_give_item(
    user_ids=user_ids,
    item_key="container_rare",
    quantity=5,
    admin_id=456
)

# Результат
{
    "success": True,
    "total": 500,
    "success_count": 498,
    "error_count": 2
}
```

### Массовое начисление ресурсов

```python
# Начислить ресурсы множеству игроков
result = await service.mass_add_resources(
    user_ids=user_ids,
    resources={
        "metal": 1000,
        "crystals": 100
    },
    admin_id=456
)

# Результат
{
    "success": True,
    "total": 500,
    "success_count": 498,
    "error_count": 2
}
```

### Подтверждение для больших операций

Для операций с более чем 100 пользователями требуется подтверждение:

```python
# Если пользователей > 100, вернётся:
{
    "success": False,
    "requires_confirmation": True,
    "token": "abc123...",
    "message": "⚠️ Требуется подтверждение для 500 пользователей"
}

# После подтверждения
confirmation = get_confirmation_service()
check = await confirmation.check_confirmation(token, admin_id)

if check["valid"]:
    # Выполняем операцию
    result = await service.mass_give_item(...)
```

### Лимиты

- Максимум пользователей за раз: **10 000**
- Максимум предметов: **100** за раз
- Максимум ресурсов: **10⁹** за раз

---

## 6. Форматирование данных

### Карточка игрока

```python
from admin import format_player_card

text = format_player_card(player_data)
```

### Краткий формат игрока

```python
from admin import format_player_short

# Результат: "🟢123456 @username (Lvl.10)"
text = format_player_short(player_data)
```

### Числа и даты

```python
from admin import format_number, format_datetime, format_date

format_number(1234567)      # "1 234 567"
format_datetime("2024-12-20T15:30:00")  # "20.12.2024 15:30"
format_date("2024-12-20T15:30:00")      # "20.12.2024"
```

---

## Статистика изменений

| Категория | Было | Стало |
|-----------|------|-------|
| Пресеты | 3 | 6 |
| Методы поиска | 1 | 2 |
| Методы статистики | 2 | 4 |
| Массовые операции | 0 | 2 |
| Форматтеры | 0 | 14 |

### Новые файлы

| Файл | Строк | Назначение |
|------|-------|------------|
| `admin/formatters.py` | ~280 | Форматирование данных |

### Обновлённые файлы

| Файл | Изменения |
|------|-----------|
| `admin/repositories.py` | +200 строк (расширенный поиск, массовые операции, статистика) |
| `admin/services.py` | +150 строк (массовые операции, статистика) |
| `admin/__init__.py` | +15 экспортов |
