"""
5.9. Рассылка сообщений
Система массовых рассылок
"""
import asyncio
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable
from datetime import datetime
from enum import Enum


class BroadcastTarget(Enum):
    """Целевая аудитория рассылки"""
    ALL = "all"                           # Все игроки
    ACTIVE_7D = "active_7d"               # Активные за 7 дней
    ACTIVE_24H = "active_24h"             # Активные за 24 часа
    PREMIUM = "premium"                   # Премиум-игроки
    BY_LEVEL = "by_level"                 # По уровню
    BY_ID_LIST = "by_id_list"             # По списку ID
    NO_CLAN = "no_clan"                   # Без клана
    IN_CLAN = "in_clan"                   # В клане


@dataclass
class BroadcastMessage:
    """Сообщение для рассылки"""
    broadcast_id: int
    text: str
    target: BroadcastTarget
    target_params: Dict = None           # Дополнительные параметры
    photo: Optional[str] = None           # URL или file_id фото
    buttons: List[Dict] = None            # Inline кнопки
    parse_mode: str = "HTML"
    
    # Статус
    status: str = "draft"                 # draft, pending, sending, completed, cancelled
    created_by: int = 0
    created_at: datetime = None
    started_at: datetime = None
    completed_at: datetime = None
    
    # Статистика
    total_recipients: int = 0
    sent_success: int = 0
    sent_failed: int = 0
    blocked_users: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.target_params is None:
            self.target_params = {}
        if self.buttons is None:
            self.buttons = []


class BroadcastSystem:
    """Система рассылки"""
    
    # Лимиты
    MAX_TEXT_LENGTH = 4096
    MAX_BUTTONS = 10
    BATCH_SIZE = 30                        # Сообщений за раз
    BATCH_DELAY = 1                        # Задержка между батчами (сек)
    
    @staticmethod
    def validate_text(text: str) -> tuple:
        """Валидация текста рассылки"""
        if not text:
            return False, "Текст не может быть пустым"
        
        if len(text) > BroadcastSystem.MAX_TEXT_LENGTH:
            return False, f"Текст слишком длинный (макс {BroadcastSystem.MAX_TEXT_LENGTH} символов)"
        
        return True, "OK"
    
    @staticmethod
    def validate_buttons(buttons: List[Dict]) -> tuple:
        """Валидация кнопок"""
        if not buttons:
            return True, "OK"
        
        if len(buttons) > BroadcastSystem.MAX_BUTTONS:
            return False, f"Слишком много кнопок (макс {BroadcastSystem.MAX_BUTTONS})"
        
        for btn in buttons:
            if "text" not in btn or "callback_data" not in btn:
                return False, "Кнопка должна содержать 'text' и 'callback_data'"
            
            if len(btn["text"]) > 40:
                return False, f"Текст кнопки слишком длинный: {btn['text']}"
            
            if len(btn["callback_data"]) > 64:
                return False, f"callback_data слишком длинный: {btn['callback_data']}"
        
        return True, "OK"
    
    @staticmethod
    async def get_recipient_count(db, target: BroadcastTarget, 
                                    params: Dict = None) -> int:
        """Получить количество получателей"""
        # Заглушка - реализация через БД запросы
        counts = {
            BroadcastTarget.ALL: 1000,
            BroadcastTarget.ACTIVE_7D: 500,
            BroadcastTarget.ACTIVE_24H: 200,
            BroadcastTarget.PREMIUM: 50,
            BroadcastTarget.NO_CLAN: 300,
            BroadcastTarget.IN_CLAN: 200,
        }
        return counts.get(target, 0)
    
    @staticmethod
    async def get_recipients(db, target: BroadcastTarget,
                              params: Dict = None,
                              offset: int = 0,
                              limit: int = 100) -> List[int]:
        """Получить список ID получателей"""
        # Заглушка - реализация через БД
        return []
    
    @staticmethod
    async def send_broadcast(bot, message: BroadcastMessage,
                               db,
                               progress_callback: Callable = None) -> Dict:
        """
        Отправка рассылки
        
        Args:
            bot: Экземпляр бота
            message: Данные рассылки
            db: База данных
            progress_callback: Функция для отчета о прогрессе
        
        Returns:
            Dict со статистикой отправки
        """
        results = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "blocked": 0,
            "errors": []
        }
        
        # Получаем получателей
        recipients = await BroadcastSystem.get_recipients(
            db, message.target, message.target_params
        )
        
        if not recipients:
            return results
        
        results["total"] = len(recipients)
        message.total_recipients = results["total"]
        message.status = "sending"
        message.started_at = datetime.now()
        
        # Отправка батчами
        for i in range(0, len(recipients), BroadcastSystem.BATCH_SIZE):
            batch = recipients[i:i + BroadcastSystem.BATCH_SIZE]
            
            for user_id in batch:
                try:
                    # Отправка сообщения
                    if message.photo:
                        await bot.send_photo(
                            chat_id=user_id,
                            photo=message.photo,
                            caption=message.text,
                            parse_mode=message.parse_mode
                        )
                    else:
                        await bot.send_message(
                            chat_id=user_id,
                            text=message.text,
                            parse_mode=message.parse_mode
                        )
                    
                    results["success"] += 1
                    message.sent_success += 1
                    
                except Exception as e:
                    results["failed"] += 1
                    message.sent_failed += 1
                    
                    error_str = str(e)
                    if "blocked" in error_str.lower() or "user is blocked" in error_str.lower():
                        results["blocked"] += 1
                        message.blocked_users += 1
                    else:
                        results["errors"].append({
                            "user_id": user_id,
                            "error": error_str
                        })
            
            # Прогресс
            if progress_callback:
                await progress_callback(
                    sent=i + len(batch),
                    total=results["total"],
                    success=results["success"],
                    failed=results["failed"]
                )
            
            # Задержка между батчами
            if i + BroadcastSystem.BATCH_SIZE < len(recipients):
                await asyncio.sleep(BroadcastSystem.BATCH_DELAY)
        
        message.status = "completed"
        message.completed_at = datetime.now()
        
        return results
    
    @staticmethod
    def format_broadcast_stats(message: BroadcastMessage) -> str:
        """Форматировать статистику рассылки"""
        text = "📢 СТАТИСТИКА РАССЫЛКИ\n\n"
        text += f"📊 Статус: {message.status.upper()}\n"
        text += f"👥 Получателей: {message.total_recipients}\n"
        text += f"✅ Отправлено: {message.sent_success}\n"
        text += f"❌ Ошибок: {message.sent_failed}\n"
        text += f"🚫 Заблокировали: {message.blocked_users}\n"
        
        if message.started_at and message.completed_at:
            duration = (message.completed_at - message.started_at).total_seconds()
            text += f"⏱ Время: {int(duration)} сек\n"
        
        return text
