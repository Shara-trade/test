# Утилиты для хендлеров

## Валидаторы

### InputValidator

Универсальный валидатор ввода пользователя.

```python
from handlers.utils import InputValidator

# Валидация целого числа
is_valid, value, error = InputValidator.validate_int(
    text="1,000",
    min_val=1,
    max_val=10000
)
# is_valid = True, value = 1000, error = ""

# Валидация с ошибкой
is_valid, value, error = InputValidator.validate_int(
    text="abc",
    min_val=1
)
# is_valid = False, value = None, error = "Введите целое число"

# Валидация username
is_valid, username, error = InputValidator.validate_username("@Test_User")
# is_valid = True, username = "test_user", error = ""

# Валидация длины текста
is_valid, text, error = InputValidator.validate_text_length(
    text="Hello world",
    min_len=1,
    max_len=100
)
```

### Пример использования в FSM

```python
from handlers.utils import InputValidator
from aiogram.fsm.context import FSMContext

@router.message(MyStates.enter_amount)
async def process_amount(message: Message, state: FSMContext):
    is_valid, amount, error = InputValidator.validate_int(
        message.text,
        min_val=1,
        max_val=1000
    )
    
    if not is_valid:
        await message.answer(f"❌ {error}")
        return
    
    # Работаем с amount
    await state.update_data(amount=amount)
    await state.set_state(MyStates.confirm)
```

---

## Пагинация

### Paginator

Универсальный класс для пагинации списков.

```python
from handlers.utils import Paginator

# Создаём пагинатор
items = await db.get_inventory(user_id)
paginator = Paginator(items, page=1, per_page=10)

# Получаем элементы текущей страницы
current_items = paginator.current_items

# Информация о странице
info = paginator.get_page_info()
# "Страница 1 из 5 (47 элементов)"

# Создаём клавиатуру с пагинацией
keyboard = paginator.get_keyboard(
    callback_prefix="inv_page",
    item_callback=lambda item, idx: {
        "text": f"{item['icon']} {item['name']} x{item['quantity']}",
        "callback_data": f"item_{item['item_id']}"
    },
    back_callback="main_menu"
)
```

### SimplePaginator

Упрощённая пагинация без кнопок элементов.

```python
from handlers.utils import SimplePaginator

paginator = SimplePaginator(items, page=1, per_page=10)

keyboard = paginator.get_nav_keyboard(
    callback_prefix="top_level",
    back_callback="main_menu"
)
```

---

## Базовые хендлеры

### BaseCallbackHandler

Базовый класс с автоматической обработкой ошибок.

```python
from handlers.utils import BaseCallbackHandler

class MyHandler(BaseCallbackHandler):
    async def _handle(self, callback: CallbackQuery, state: FSMContext):
        # Ваша логика
        user = await db.get_user(callback.from_user.id)
        await callback.message.edit_text(f"Привет, {user['username']}!")

# Регистрация
handler = MyHandler()
router.callback_query(F.data == "my_action")(handler.handle)
```

### BaseFSMHandler

Базовый класс для FSM с валидацией.

```python
from handlers.utils import BaseFSMHandler, InputValidator

class AmountHandler(BaseFSMHandler):
    validator = InputValidator.validate_int
    
    async def _handle_message(self, message: Message, state: FSMContext):
        is_valid, amount, error = await self.validate_input(message.text)
        
        if not is_valid:
            await message.answer(f"❌ {error}")
            return
        
        # Работаем с amount
        await state.update_data(amount=amount)
```

---

## Вспомогательные функции

```python
from handlers.utils import format_number, format_time_delta, truncate_text

# Форматирование числа
format_number(1234567)  # "1 234 567"

# Форматирование времени
format_time_delta(3665)  # "1 ч 1 мин"
format_time_delta(90061)  # "1 д 1 ч"

# Обрезка текста
truncate_text("Очень длинный текст...", max_len=20)
# "Очень длинный тек..."
```

---

## Примеры

### Топ с пагинацией

```python
async def show_top(user_id: int, category: str, page: int = 1):
    # Получаем данные
    players = await get_top_players(category)
    
    # Создаём пагинатор
    paginator = SimplePaginator(players, page=page, per_page=10)
    
    # Формируем текст
    text = "🏆 <b>ТОП ИГРОКОВ</b>\n\n"
    
    for i, player in enumerate(paginator.current_items):
        rank = (page - 1) * 10 + i + 1
        text += f"{rank}. @{player['username']} — Ур. {player['level']}\n"
    
    text += f"\n{paginator.get_page_info()}"
    
    # Клавиатура
    keyboard = paginator.get_nav_keyboard(
        callback_prefix=f"top_{category}",
        back_callback="main_menu"
    )
    
    return text, keyboard
```

### Валидация формы

```python
class FormStates(StatesGroup):
    enter_name = State()
    enter_age = State()
    enter_email = State()

@router.message(FormStates.enter_name)
async def process_name(message: Message, state: FSMContext):
    is_valid, name, error = InputValidator.validate_text_length(
        message.text, min_len=2, max_len=50
    )
    
    if not is_valid:
        await message.answer(f"❌ {error}")
        return
    
    await state.update_data(name=name)
    await state.set_state(FormStates.enter_age)
    await message.answer("Введите возраст:")

@router.message(FormStates.enter_age)
async def process_age(message: Message, state: FSMContext):
    is_valid, age, error = InputValidator.validate_int(
        message.text, min_val=1, max_val=150
    )
    
    if not is_valid:
        await message.answer(f"❌ {error}")
        return
    
    await state.update_data(age=age)
    await state.set_state(FormStates.enter_email)
    await message.answer("Введите email:")
```
