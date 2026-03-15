 # Безопасность админ-панели (Пункт 2 ТЗ)

## Обзор

Реализована многоуровневая система безопасности для админ-панели:

1. **Декораторы проверки прав** — контроль доступа
2. **Подпись callback_data** — защита от подделки
3. **Валидация через Pydantic** — проверка данных
4. **Rate Limiting** — защита от массовых операций
5. **Подтверждение действий** — для критичных операций
6. **Аудит** — логирование всех действий

---

## 1. Декораторы проверки прав

### Использование

```python
from admin.decorators import admin_required, AdminFilter

# Вариант 1: Декоратор
@router.callback_query(F.data == "admin:players")
@admin_required("players")
async def admin_players_menu(callback: CallbackQuery):
    ...

# Вариант 2: Фильтр
@router.callback_query(AdminFilter(permission="economy"))
async def admin_economy_menu(callback: CallbackQuery):
    ...

# Вариант 3: Ручная проверка
if not await is_admin(user_id):
    await callback.answer("⛔ Нет доступа")
    return

if not await check_permission(user_id, "players"):
    await callback.answer("⛔ Недостаточно прав")
    return
```

### Права по ролям

| Роль | Права |
|------|-------|
| `owner` | Все права |
| `senior` | players, containers, modules, drop, economy, materials, stats, logs, testing, events, backups, metrics |
| `moderator` | players, containers, modules, materials, stats, logs |
| `support` | stats, logs |

---

## 2. Подпись callback_data

### Использование

```python
from core.security import create_safe_callback
from admin.safe_keyboards import SafeKeyboardBuilder

# Создание подписанного callback
safe_callback = create_safe_callback(user_id, "admin:players:ban:123")

# Использование SafeKeyboardBuilder
keyboard = (
    SafeKeyboardBuilder(user_id)
    .row("Бан", "admin:players:ban:123")
    .build()
)
```

### Как это работает

1. При создании кнопки callback подписывается HMAC-SHA256
2. При нажатии middleware проверяет подпись
3. Если подпись не совпадает — действие блокируется

---

## 3. Валидация через Pydantic

### Доступные схемы

```python
from admin.schemas import (
    ResourceUpdateSchema,      # Изменение ресурсов
    GiveContainerSchema,       # Выдача контейнеров
    GiveMaterialSchema,        # Выдача материалов
    GiveModuleSchema,          # Выдача модулей
    BanPlayerSchema,           # Бан игрока
    PlayerSearchSchema,        # Поиск игрока
)
```

### Пример использования

```python
from admin.schemas import GiveContainerSchema
from pydantic import ValidationError

try:
    schema = GiveContainerSchema(
        user_id=123,
        container_type="rare",
        quantity=5
    )
except ValidationError as e:
    await callback.answer(f"❌ {e.errors()[0]['msg']}")
    return

# Используем валидированные данные
await service.give_container(
    user_id=schema.user_id,
    container_type=schema.container_type.value,
    quantity=schema.quantity
)
```

### Лимиты валидации

| Поле | Мин | Макс |
|------|-----|------|
| metal, crystals | 0 | 10¹² |
| dark_matter | 0 | 10⁹ |
| container quantity | 1 | 100 |
| material quantity | 1 | 1000 |
| ban duration | 1 час | 8760 часов (1 год) |

---

## 4. Rate Limiting

### Лимиты по умолчанию

| Действие | Лимит | Окно |
|----------|-------|------|
| edit_resource | 50 | 1 час |
| give_item | 100 | 1 час |
| give_container | 50 | 1 час |
| give_module | 30 | 1 час |
| ban_player | 20 | 1 час |
| mass_operation | 3 | 1 час |

### Подключение

```python
# В main.py
from admin import get_rate_limit_middleware

rate_limit_mw = get_rate_limit_middleware()
dp.callback_query.middleware(rate_limit_mw)
```

### Кастомизация

```python
# В admin/middleware.py
RATE_LIMITS = {
    "ban_player": {"max": 20, "window": 3600},
    "mass_operation": {"max": 3, "window": 3600},
    ...
}
```

---

## 5. Подтверждение опасных действий

### Использование

```python
from admin import get_confirmation_service

confirmation_service = get_confirmation_service()

# Запрос подтверждения
token = await confirmation_service.request_confirmation(
    user_id=admin_id,
    action="ban_player",
    data={"target_user_id": 123}
)

# Показываем кнопки с токеном
keyboard = SafeKeyboardBuilder(admin_id).confirm_buttons(
    f"admin:ban:confirm:{token}",
    f"admin:ban:cancel:{token}"
).build()

# Проверка подтверждения
result = await confirmation_service.check_confirmation(token, admin_id)
if result["valid"]:
    # Выполняем действие
    ...
```

### Срок действия

- Токен подтверждения действует **60 секунд**
- После использования токен удаляется

---

## 6. Аудит действий

### Автоматическое логирование

Middleware `AdminAuditMiddleware` автоматически логирует все админ-действия:

- admin_id — кто выполнил
- action — тип действия
- target_user_id — над кем выполнено
- details — детали (callback_data)
- created_at — время

### Просмотр логов

```python
from admin import get_admin_service

service = get_admin_service(DATABASE_PATH)
logs = await service.get_logs(limit=50, action="ban_player")
```

---

## Чек-лист внедрения

### ✅ Обязательно

1. [ ] Добавить `@admin_required()` во все обработчики админ-панели
2. [ ] Использовать `SafeKeyboardBuilder` для критичных кнопок
3. [ ] Валидировать все входные данные через Pydantic
4. [ ] Добавить подтверждение для бана и удаления
5. [ ] Подключить middleware в `main.py`

### ⚠️ Рекомендуется

1. [ ] Подписывать callback_data для операций с ресурсами
2. [ ] Логировать все критичные действия
3. [ ] Использовать Rate Limiting для массовых операций

---

## Примеры кода

Полные примеры использования см. в файле:
- `admin/security_examples.py`

---

## Тестирование

```bash
# Проверка импортов
python -c "from admin import admin_required, AdminRateLimitMiddleware; print('OK')"

# Проверка валидации
python -c "
from admin.schemas import GiveContainerSchema
schema = GiveContainerSchema(user_id=1, container_type='rare', quantity=5)
print(f'Valid: {schema.quantity}')
"
```
