"""
Утилиты для создания безопасных клавиатур админ-панели
Используют подпись callback_data для защиты от подделки
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Optional

from core.security import create_safe_callback


class SafeKeyboardBuilder:
    """
    Билдер для безопасных клавиатур с подписанными callback_data.
    
    Usage:
        builder = SafeKeyboardBuilder(user_id=123456)
        builder.row("Текст", "admin:players:card:789")
        keyboard = builder.build()
    """
    
    def __init__(self, user_id: Optional[int] = None, sign: bool = True):
        """
        Инициализация билдера.
        
        Args:
            user_id: ID пользователя для подписи
            sign: Подписывать ли callback_data
        """
        self.builder = InlineKeyboardBuilder()
        self.user_id = user_id
        self.sign = sign
    
    def _make_callback(self, callback_data: str) -> str:
        """Создать (подписанный) callback_data"""
        if self.sign and self.user_id and callback_data != "ignore":
            return create_safe_callback(self.user_id, callback_data)
        return callback_data
    
    def row(self, *buttons) -> 'SafeKeyboardBuilder':
        """
        Добавить ряд кнопок.
        
        Args:
            *buttons: Кортежи (text, callback_data) или InlineKeyboardButton
        
        Returns:
            self для chaining
        """
        row_buttons = []
        
        for btn in buttons:
            if isinstance(btn, InlineKeyboardButton):
                row_buttons.append(btn)
            elif isinstance(btn, tuple):
                text, callback = btn
                safe_callback = self._make_callback(callback)
                row_buttons.append(
                    InlineKeyboardButton(text=text, callback_data=safe_callback)
                )
            elif isinstance(btn, dict):
                text = btn.get("text")
                callback = btn.get("callback_data")
                if text and callback:
                    safe_callback = self._make_callback(callback)
                    row_buttons.append(
                        InlineKeyboardButton(text=text, callback_data=safe_callback)
                    )
        
        if row_buttons:
            self.builder.row(*row_buttons)
        
        return self
    
    def back_button(self, callback_data: str = "admin:main") -> 'SafeKeyboardBuilder':
        """Добавить кнопку назад"""
        safe_callback = self._make_callback(callback_data)
        self.builder.row(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=safe_callback)
        )
        return self
    
    def close_button(self) -> 'SafeKeyboardBuilder':
        """Добавить кнопку закрытия"""
        callback = self._make_callback("admin:close")
        self.builder.row(
            InlineKeyboardButton(text="❌ Закрыть", callback_data=callback)
        )
        return self
    
    def confirm_buttons(
        self, 
        confirm_callback: str, 
        cancel_callback: str
    ) -> 'SafeKeyboardBuilder':
        """Добавить кнопки подтверждения/отмены"""
        self.builder.row(
            InlineKeyboardButton(
                text="✅ Подтвердить", 
                callback_data=self._make_callback(confirm_callback)
            ),
            InlineKeyboardButton(
                text="❌ Отмена", 
                callback_data=self._make_callback(cancel_callback)
            )
        )
        return self
    
    def build(self) -> InlineKeyboardMarkup:
        """Построить клавиатуру"""
        return self.builder.as_markup()


def create_safe_button(
    user_id: int,
    text: str,
    callback_data: str
) -> InlineKeyboardButton:
    """
    Создать безопасную inline-кнопку.
    
    Args:
        user_id: ID пользователя
        text: Текст кнопки
        callback_data: Callback данные
    
    Returns:
        InlineKeyboardButton с подписанным callback_data
    """
    safe_callback = create_safe_callback(user_id, callback_data)
    return InlineKeyboardButton(text=text, callback_data=safe_callback)


def make_safe_keyboard(
    user_id: int,
    buttons: list,
    sign: bool = True
) -> InlineKeyboardMarkup:
    """
    Создать безопасную клавиатуру из списка кнопок.
    
    Args:
        user_id: ID пользователя
        buttons: Список списков кнопок [[(text, callback), ...], ...]
        sign: Подписывать ли callback_data
    
    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()
    
    for row in buttons:
        row_buttons = []
        for btn in row:
            if isinstance(btn, tuple):
                text, callback = btn
                if sign:
                    callback = create_safe_callback(user_id, callback)
                row_buttons.append(
                    InlineKeyboardButton(text=text, callback_data=callback)
                )
            elif isinstance(btn, InlineKeyboardButton):
                row_buttons.append(btn)
        
        if row_buttons:
            builder.row(*row_buttons)
    
    return builder.as_markup()
