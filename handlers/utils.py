"""
Утилиты для хендлеров.
Базовые классы, валидаторы, пагинация.
"""
from typing import Optional, Tuple, List, Any, Callable
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging


# ==================== ВАЛИДАТОРЫ ====================

class InputValidator:
    """Универсальный валидатор ввода"""
    
    @staticmethod
    def validate_int(
        text: str, 
        min_val: Optional[int] = None, 
        max_val: Optional[int] = None,
        allow_negative: bool = False
    ) -> Tuple[bool, Optional[int], str]:
        """
        Валидация целого числа.
        
        Args:
            text: Входной текст
            min_val: Минимальное значение (опционально)
            max_val: Максимальное значение (опционально)
            allow_negative: Разрешить отрицательные числа
        
        Returns:
            (is_valid, value, error_message)
        """
        try:
            # Очищаем текст от пробелов и разделителей
            cleaned = text.replace(" ", "").replace(",", "").replace(".", "")
            value = int(cleaned)
            
            if not allow_negative and value < 0:
                return False, None, "Значение не может быть отрицательным"
            
            if min_val is not None and value < min_val:
                return False, None, f"Значение должно быть не менее {min_val:,}"
            
            if max_val is not None and value > max_val:
                return False, None, f"Значение должно быть не более {max_val:,}"
            
            return True, value, ""
            
        except ValueError:
            return False, None, "Введите целое число"
    
    @staticmethod
    def validate_float(
        text: str,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        allow_negative: bool = False
    ) -> Tuple[bool, Optional[float], str]:
        """
        Валидация числа с плавающей точкой.
        
        Returns:
            (is_valid, value, error_message)
        """
        try:
            cleaned = text.replace(" ", "").replace(",", ".")
            value = float(cleaned)
            
            if not allow_negative and value < 0:
                return False, None, "Значение не может быть отрицательным"
            
            if min_val is not None and value < min_val:
                return False, None, f"Значение должно быть не менее {min_val}"
            
            if max_val is not None and value > max_val:
                return False, None, f"Значение должно быть не более {max_val}"
            
            return True, value, ""
            
        except ValueError:
            return False, None, "Введите число"
    
    @staticmethod
    def validate_username(text: str) -> Tuple[bool, Optional[str], str]:
        """
        Валидация username (без @).
        
        Returns:
            (is_valid, cleaned_username, error_message)
        """
        cleaned = text.strip().lstrip("@").lower()
        
        if not cleaned:
            return False, None, "Введите username"
        
        if len(cleaned) < 3:
            return False, None, "Username слишком короткий (минимум 3 символа)"
        
        if len(cleaned) > 32:
            return False, None, "Username слишком длинный (максимум 32 символа)"
        
        # Проверка символов
        import re
        if not re.match(r'^[a-z0-9_]+$', cleaned):
            return False, None, "Username может содержать только буквы, цифры и _"
        
        return True, cleaned, ""
    
    @staticmethod
    def validate_text_length(
        text: str,
        min_len: int = 1,
        max_len: int = 1000
    ) -> Tuple[bool, Optional[str], str]:
        """
        Валидация длины текста.
        
        Returns:
            (is_valid, cleaned_text, error_message)
        """
        cleaned = text.strip()
        
        if len(cleaned) < min_len:
            return False, None, f"Минимум {min_len} символов"
        
        if len(cleaned) > max_len:
            return False, None, f"Максимум {max_len} символов"
        
        return True, cleaned, ""


# ==================== ПАГИНАЦИЯ ====================

class Paginator:
    """
    Универсальный класс для пагинации списков.
    
    Usage:
        items = await db.get_inventory(user_id)
        paginator = Paginator(items, page=1, per_page=10)
        
        text = format_items(paginator.current_items)
        keyboard = paginator.get_keyboard("inv_page")
    """
    
    def __init__(
        self, 
        items: List[Any], 
        page: int = 1, 
        per_page: int = 10,
        max_buttons: int = 5
    ):
        self.items = items
        self.per_page = per_page
        self.max_buttons = max_buttons
        self.page = max(1, min(page, self.total_pages))
    
    @property
    def total_pages(self) -> int:
        """Общее количество страниц"""
        if not self.items:
            return 1
        return max(1, (len(self.items) + self.per_page - 1) // self.per_page)
    
    @property
    def current_items(self) -> List[Any]:
        """Элементы текущей страницы"""
        if not self.items:
            return []
        start = (self.page - 1) * self.per_page
        end = start + self.per_page
        return self.items[start:end]
    
    @property
    def total_items(self) -> int:
        """Общее количество элементов"""
        return len(self.items)
    
    @property
    def has_prev(self) -> bool:
        """Есть ли предыдущая страница"""
        return self.page > 1
    
    @property
    def has_next(self) -> bool:
        """Есть ли следующая страница"""
        return self.page < self.total_pages
    
    @property
    def range_start(self) -> int:
        """Начальный индекс (1-based)"""
        return (self.page - 1) * self.per_page + 1
    
    @property
    def range_end(self) -> int:
        """Конечный индекс (1-based)"""
        return min(self.page * self.per_page, self.total_items)
    
    def get_page_info(self) -> str:
        """Текстовая информация о странице"""
        return f"Страница {self.page} из {self.total_pages} ({self.total_items} элементов)"
    
    def get_keyboard(
        self,
        callback_prefix: str,
        item_callback: Callable[[Any, int], dict] = None,
        back_callback: str = None,
        additional_buttons: List[List[dict]] = None
    ) -> InlineKeyboardMarkup:
        """
        Создать клавиатуру с пагинацией.
        
        Args:
            callback_prefix: Префикс для callback_data (например, "inv_page")
            item_callback: Функция для создания кнопки элемента (item, index) -> dict
            back_callback: Callback для кнопки "Назад"
            additional_buttons: Дополнительные кнопки перед навигацией
        
        Returns:
            InlineKeyboardMarkup
        """
        builder = InlineKeyboardBuilder()
        
        # Кнопки элементов
        if item_callback:
            for i, item in enumerate(self.current_items):
                btn_data = item_callback(item, (self.page - 1) * self.per_page + i)
                if btn_data:
                    builder.button(
                        text=btn_data.get('text', str(item)),
                        callback_data=btn_data.get('callback_data', f"{callback_prefix}_item_{i}")
                    )
        
        builder.adjust(1)  # По одной кнопке в строке для элементов
        
        # Дополнительные кнопки
        if additional_buttons:
            for row in additional_buttons:
                for btn in row:
                    builder.button(**btn)
            builder.adjust(1)
        
        # Навигация
        nav_buttons = []
        
        if self.total_pages > 1:
            # Кнопки навигации по страницам
            if self.has_prev:
                nav_buttons.append({
                    "text": "◀️",
                    "callback_data": f"{callback_prefix}_{self.page - 1}"
                })
            
            # Номера страниц
            start_page = max(1, self.page - self.max_buttons // 2)
            end_page = min(self.total_pages, start_page + self.max_buttons - 1)
            
            if start_page > 1:
                nav_buttons.append({
                    "text": "1",
                    "callback_data": f"{callback_prefix}_1"
                })
                if start_page > 2:
                    nav_buttons.append({"text": "...", "callback_data": "noop"})
            
            for p in range(start_page, end_page + 1):
                if p == self.page:
                    nav_buttons.append({
                        "text": f"[{p}]",
                        "callback_data": "noop"
                    })
                else:
                    nav_buttons.append({
                        "text": str(p),
                        "callback_data": f"{callback_prefix}_{p}"
                    })
            
            if end_page < self.total_pages:
                if end_page < self.total_pages - 1:
                    nav_buttons.append({"text": "...", "callback_data": "noop"})
                nav_buttons.append({
                    "text": str(self.total_pages),
                    "callback_data": f"{callback_prefix}_{self.total_pages}"
                })
            
            if self.has_next:
                nav_buttons.append({
                    "text": "▶️",
                    "callback_data": f"{callback_prefix}_{self.page + 1}"
                })
        
        # Добавляем навигацию
        for btn in nav_buttons:
            builder.button(**btn)
        
        if nav_buttons:
            builder.adjust(len(nav_buttons))
        
        # Кнопка "Назад"
        if back_callback:
            builder.button(text="⬅️ Назад", callback_data=back_callback)
            builder.adjust(1)
        
        return builder.as_markup()


class SimplePaginator(Paginator):
    """
    Упрощённая пагинация без кнопок элементов.
    Только навигация по страницам.
    """
    
    def get_nav_keyboard(
        self,
        callback_prefix: str,
        back_callback: str = None
    ) -> InlineKeyboardMarkup:
        """
        Создать только клавиатуру навигации.
        
        Args:
            callback_prefix: Префикс для callback_data
            back_callback: Callback для кнопки "Назад"
        
        Returns:
            InlineKeyboardMarkup
        """
        builder = InlineKeyboardBuilder()
        
        nav_buttons = []
        
        if self.has_prev:
            nav_buttons.append({
                "text": "◀️ Назад",
                "callback_data": f"{callback_prefix}_{self.page - 1}"
            })
        
        nav_buttons.append({
            "text": f"{self.page}/{self.total_pages}",
            "callback_data": "noop"
        })
        
        if self.has_next:
            nav_buttons.append({
                "text": "Вперёд ▶️",
                "callback_data": f"{callback_prefix}_{self.page + 1}"
            })
        
        for btn in nav_buttons:
            builder.button(**btn)
        
        builder.adjust(3)
        
        if back_callback:
            builder.button(text="⬅️ В меню", callback_data=back_callback)
            builder.adjust(1)
        
        return builder.as_markup()


# ==================== БАЗОВЫЙ ХЕНДЛЕР ====================

class BaseCallbackHandler:
    """
    Базовый класс для callback-хендлеров с обработкой ошибок.
    
    Usage:
        class MyHandler(BaseCallbackHandler):
            async def _handle(self, callback: CallbackQuery, state: FSMContext):
                # Ваша логика
                await callback.message.edit_text("Done")
        
        handler = MyHandler()
        router.callback_query(F.data == "my_action")(handler.handle)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def handle(self, callback: CallbackQuery, state: FSMContext = None):
        """Точка входа с обработкой ошибок"""
        try:
            result = await self._handle(callback, state)
            return result
        except Exception as e:
            self.logger.error(f"Error in {self.__class__.__name__}: {e}", exc_info=True)
            await self._handle_error(callback, e)
    
    async def _handle(self, callback: CallbackQuery, state: FSMContext):
        """Переопределить в наследниках"""
        raise NotImplementedError
    
    async def _handle_error(self, callback: CallbackQuery, error: Exception):
        """Обработка ошибки"""
        try:
            await callback.answer(
                "❌ Произошла ошибка. Попробуйте позже.",
                show_alert=True
            )
        except:
            pass


class BaseFSMHandler(BaseCallbackHandler):
    """
    Базовый класс для FSM-хендлеров с валидацией.
    
    Usage:
        class MyFSMHandler(BaseFSMHandler):
            validator = InputValidator.validate_int
            
            async def _handle_message(self, message: Message, state: FSMContext):
                is_valid, value, error = await self.validate_input(message.text)
                
                if not is_valid:
                    await message.answer(f"❌ {error}")
                    return
                
                # Работаем с value
    """
    
    validator: Callable = None
    
    async def validate_input(self, text: str) -> Tuple[bool, Any, str]:
        """Валидация ввода через назначенный валидатор"""
        if self.validator is None:
            return True, text, ""
        return self.validator(text)
    
    async def _handle(self, callback: CallbackQuery, state: FSMContext):
        """Callback не используется в FSM"""
        pass
    
    async def handle_message(self, message: Message, state: FSMContext):
        """Точка входа для message-хендлеров"""
        try:
            result = await self._handle_message(message, state)
            return result
        except Exception as e:
            self.logger.error(f"Error in {self.__class__.__name__}: {e}", exc_info=True)
            await message.answer("❌ Произошла ошибка. Попробуйте позже.")
    
    async def _handle_message(self, message: Message, state: FSMContext):
        """Переопределить в наследниках"""
        raise NotImplementedError


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def format_number(n: int) -> str:
    """Форматирование числа с разделителями"""
    return f"{n:,}".replace(",", " ")


def format_time_delta(seconds: int) -> str:
    """Форматирование времени в человекочитаемый вид"""
    if seconds < 60:
        return f"{seconds} сек"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} мин"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours} ч {minutes} мин"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days} д {hours} ч"


def truncate_text(text: str, max_len: int = 200) -> str:
    """Обрезать текст с многоточием"""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."
