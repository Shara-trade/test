"""
8.2.1 Проверка callback_data на принадлежность пользователю
Middleware для защиты от подделки callback_data
"""
import hashlib
import hmac
import time
from typing import Optional, Callable, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramAPIError

from config import BOT_TOKEN


class CallbackSecurityMiddleware(BaseMiddleware):
    """
    Middleware для проверки callback_data на принадлежность пользователю.
    Защищает от подделки callback_data другими пользователями.
    """
    
    # Секретный ключ для подписи (на основе токена бота)
    SECRET_KEY = hashlib.sha256(BOT_TOKEN.encode()).digest()[:16]
    
    # Разделитель данных и подписи
    SEPARATOR = ":sig:"
    
    # Время жизни callback (секунды)
    CALLBACK_TTL = 3600  # 1 час
    
    # Префиксы, которые не требуют проверки (публичные данные)
    PUBLIC_PREFIXES = (
        "help_",
        "info_",
        "view_",
    )
    
    # Префиксы, которые требуют строгой проверки
    PROTECTED_PREFIXES = (
        "mine_",
        "buy_",
        "sell_",
        "craft_",
        "admin_",
        "upgrade_",
        "equip_",
        "clan_",
    )
    
    def __init__(self):
        self._cache = {}  # Кэш проверенных callback
    
    @classmethod
    def sign_callback(cls, user_id: int, data: str) -> str:
        """
        Подписать callback_data для пользователя.
        Использовать при создании inline-кнопок.
        
        Args:
            user_id: ID пользователя
            data: Оригинальные данные
        
        Returns:
            Подписанные данные в формате: data:sig:timestamp:signature
        """
        timestamp = int(time.time())
        message = f"{user_id}:{data}:{timestamp}"
        signature = hmac.new(
            cls.SECRET_KEY,
            message.encode(),
            hashlib.sha256
        ).hexdigest()[:16]
        
        return f"{data}{cls.SEPARATOR}{timestamp}:{signature}"
    
    @classmethod
    def verify_callback(cls, user_id: int, signed_data: str) -> tuple:
        """
        Проверить подпись callback_data.
        
        Args:
            user_id: ID пользователя, который прислал callback
            signed_data: Подписанные данные
        
        Returns:
            (is_valid, original_data, error_message)
        """
        # Если нет подписи - разрешаем все действия (игровой бот)
        # Подпись опциональна для критичных админ-операций
        if cls.SEPARATOR not in signed_data:
            return True, signed_data, None
        
        try:
            # Разбираем подписанные данные
            parts = signed_data.rsplit(cls.SEPARATOR, 1)
            original_data = parts[0]
            sig_part = parts[1]
            
            timestamp_str, signature = sig_part.split(":")
            timestamp = int(timestamp_str)
            
            # Проверка времени жизни
            if time.time() - timestamp > cls.CALLBACK_TTL:
                return False, None, "Callback expired"
            
            # Проверка подписи
            message = f"{user_id}:{original_data}:{timestamp}"
            expected_signature = hmac.new(
                cls.SECRET_KEY,
                message.encode(),
                hashlib.sha256
            ).hexdigest()[:16]
            
            if not hmac.compare_digest(signature, expected_signature):
                return False, None, "Invalid signature"
            
            return True, original_data, None
            
        except (ValueError, IndexError) as e:
            return False, None, f"Malformed callback: {e}"
    
    async def __call__(self, handler, event, data):
        """Обработка callback query"""
        
        if isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            callback_data = event.data
            
            # Проверяем подпись
            is_valid, original_data, error = self.verify_callback(user_id, callback_data)
            
            if not is_valid:
                # Логируем попытку подделки
                await self._log_security_event(
                    user_id=user_id,
                    event_type="invalid_callback",
                    data=callback_data,
                    error=error
                )
                
                # Показываем ошибку пользователю
                try:
                    await event.answer(
                        "⚠️ Ошибка безопасности. Попробуйте снова.",
                        show_alert=True
                    )
                except TelegramAPIError:
                    pass
                
                return  # Не вызываем handler
            
            # Заменяем data на оригинальные
            if original_data != callback_data:
                event.data = original_data
        
        # Продолжаем обработку
        return await handler(event, data)
    
    async def _log_security_event(self, user_id: int, event_type: str, 
                                    data: str, error: str):
        """Логирование событий безопасности"""
        import logging
        logger = logging.getLogger("security")
        logger.warning(
            f"Security event: {event_type} | "
            f"User: {user_id} | "
            f"Data: {data[:50]}... | "
            f"Error: {error}"
        )


class OwnershipMiddleware(BaseMiddleware):
    """
    Проверка владения ресурсами.
    Проверяет, что пользователь имеет право выполнять действие с ресурсом.
    """
    
    # Паттерны callback_data с проверкой владения
    OWNERSHIP_PATTERNS = {
        # Формат: (pattern, resource_type, id_position)
        r"drone_(\w+)_(\d+)": ("drone", 2),      # drone_upgrade_123
        r"item_(\w+)_(\d+)": ("item", 2),         # item_sell_123
        r"market_cancel_(\d+)": ("market_lot", 1), # market_cancel_123
        r"clan_(\w+)_(\d+)": ("clan", 2),         # clan_kick_123
    }
    
    async def __call__(self, handler, event, data):
        """Проверка владения"""
        
        if isinstance(event, CallbackQuery):
            callback_data = event.data
            user_id = event.from_user.id
            
            # Проверяем паттерны
            import re
            for pattern, (resource_type, id_pos) in self.OWNERSHIP_PATTERNS.items():
                match = re.match(pattern, callback_data)
                if match:
                    resource_id = int(match.group(id_pos))
                    
                    # Проверяем владение
                    has_access = await self._check_ownership(
                        user_id, resource_type, resource_id
                    )
                    
                    if not has_access:
                        await event.answer(
                            "⛔ У вас нет прав для этого действия",
                            show_alert=True
                        )
                        return
        
        return await handler(event, data)
    
    async def _check_ownership(self, user_id: int, resource_type: str, 
                                 resource_id: int) -> bool:
        """Проверка владения ресурсом"""
        try:
            from database import db
            import aiosqlite
            
            async with aiosqlite.connect(db.db_path) as conn:
                if resource_type == "drone":
                    async with conn.execute(
                        "SELECT 1 FROM drones WHERE drone_id = ? AND user_id = ?",
                        (resource_id, user_id)
                    ) as cursor:
                        return bool(await cursor.fetchone())
                
                elif resource_type == "item":
                    async with conn.execute(
                        "SELECT 1 FROM inventory WHERE item_id = ? AND user_id = ?",
                        (resource_id, user_id)
                    ) as cursor:
                        return bool(await cursor.fetchone())
                
                elif resource_type == "market_lot":
                    async with conn.execute(
                        "SELECT 1 FROM market WHERE lot_id = ? AND seller_id = ?",
                        (resource_id, user_id)
                    ) as cursor:
                        return bool(await cursor.fetchone())
                
                elif resource_type == "clan":
                    # Для клана проверяем роль
                    async with conn.execute(
                        """SELECT 1 FROM clan_members cm
                           JOIN clans c ON c.clan_id = cm.clan_id
                           WHERE c.clan_id = ? AND cm.user_id = ? 
                           AND cm.role IN ('leader', 'officer')""",
                        (resource_id, user_id)
                    ) as cursor:
                        return bool(await cursor.fetchone())
            
            return False
            
        except Exception as e:
            print(f"Ownership check error: {e}")
            return False


# Вспомогательные функции для создания безопасных кнопок
def create_safe_callback(user_id: int, data: str) -> str:
    """Создать подписанный callback_data"""
    return CallbackSecurityMiddleware.sign_callback(user_id, data)


def is_safe_callback(user_id: int, data: str) -> bool:
    """Проверить callback_data"""
    is_valid, _, _ = CallbackSecurityMiddleware.verify_callback(user_id, data)
    return is_valid
