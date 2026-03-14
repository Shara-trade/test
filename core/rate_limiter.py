"""
8.2.2, 8.2.3 Защита от накруток и лимиты на действия
Rate limiting и анти-спам система
"""
import time
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum


class ActionType(Enum):
    """Типы действий для лимитирования"""
    CLICK = "click"                    # Клик по астероиду
    MINE = "mine"                      # Добыча
    BUY_DRONE = "buy_drone"            # Покупка дрона
    SELL_MARKET = "sell_market"        # Продажа на рынке
    BUY_MARKET = "buy_market"          # Покупка на рынке
    CRAFT = "craft"                    # Крафт
    OPEN_CONTAINER = "open_container"  # Открытие контейнера
    SEND_EXPEDITION = "send_expedition" # Отправка экспедиции
    CREATE_CLAN = "create_clan"        # Создание клана
    MESSAGE = "message"                # Отправка сообщения
    CALLBACK = "callback"              # Нажатие inline-кнопки


@dataclass
class RateLimit:
    """Лимит на действие"""
    max_actions: int           # Максимум действий
    period_seconds: int        # За период (секунды)
    cooldown_seconds: int = 0  # Кулдаун между действиями
    
    # Штрафы за превышение
    block_duration: int = 60   # Блокировка на N секунд
    warn_threshold: float = 0.8  # Предупреждение при 80% лимита


@dataclass
class UserActionHistory:
    """История действий пользователя"""
    user_id: int
    action_type: ActionType
    timestamps: List[float] = field(default_factory=list)
    last_warning: float = 0
    blocked_until: float = 0
    violations: int = 0


class RateLimiter:
    """Система ограничения действий"""
    
    # Лимиты по умолчанию для каждого типа действий
    DEFAULT_LIMITS = {
        ActionType.CLICK: RateLimit(
            max_actions=100,         # 100 кликов
            period_seconds=60,       # в минуту
            cooldown_seconds=0,      # без кулдауна
            block_duration=30        # блок на 30 сек при превышении
        ),
        ActionType.MINE: RateLimit(
            max_actions=100,
            period_seconds=60,
            cooldown_seconds=0,
            block_duration=30
        ),
        ActionType.BUY_DRONE: RateLimit(
            max_actions=10,
            period_seconds=60,
            cooldown_seconds=1,      # 1 сек между покупками
            block_duration=60
        ),
        ActionType.SELL_MARKET: RateLimit(
            max_actions=20,
            period_seconds=300,      # 20 продаж за 5 минут
            cooldown_seconds=2,
            block_duration=120
        ),
        ActionType.BUY_MARKET: RateLimit(
            max_actions=10,
            period_seconds=60,
            cooldown_seconds=1,
            block_duration=60
        ),
        ActionType.CRAFT: RateLimit(
            max_actions=30,
            period_seconds=60,
            cooldown_seconds=0.5,
            block_duration=60
        ),
        ActionType.OPEN_CONTAINER: RateLimit(
            max_actions=10,
            period_seconds=60,
            cooldown_seconds=1,
            block_duration=60
        ),
        ActionType.SEND_EXPEDITION: RateLimit(
            max_actions=5,
            period_seconds=300,
            cooldown_seconds=5,
            block_duration=300
        ),
        ActionType.CREATE_CLAN: RateLimit(
            max_actions=1,
            period_seconds=86400,    # 1 создание в сутки
            cooldown_seconds=0,
            block_duration=86400
        ),
        ActionType.MESSAGE: RateLimit(
            max_actions=30,
            period_seconds=60,
            cooldown_seconds=0,
            block_duration=120
        ),
        ActionType.CALLBACK: RateLimit(
            max_actions=60,
            period_seconds=60,
            cooldown_seconds=0,
            block_duration=30
        ),
    }
    
    def __init__(self):
        self._history: Dict[Tuple[int, ActionType], UserActionHistory] = {}
        self._lock = asyncio.Lock()
        
        # Переопределения лимитов (можно менять через админку)
        self._custom_limits: Dict[ActionType, RateLimit] = {}
    
    def get_limit(self, action_type: ActionType) -> RateLimit:
        """Получить лимит для действия"""
        return self._custom_limits.get(action_type, 
                                       self.DEFAULT_LIMITS.get(action_type))
    
    def set_limit(self, action_type: ActionType, limit: RateLimit):
        """Установить кастомный лимит"""
        self._custom_limits[action_type] = limit
    
    async def check_action(self, user_id: int, action_type: ActionType) -> Tuple[bool, Optional[str]]:
        """
        Проверить, можно ли выполнить действие.
        
        Returns:
            (allowed, error_message)
        """
        async with self._lock:
            limit = self.get_limit(action_type)
            if not limit:
                return True, None
            
            key = (user_id, action_type)
            now = time.time()
            
            # Получаем или создаём историю
            history = self._history.get(key)
            if history is None:
                history = UserActionHistory(
                    user_id=user_id,
                    action_type=action_type
                )
                self._history[key] = history
            
            # Проверяем блокировку
            if history.blocked_until > now:
                remaining = int(history.blocked_until - now)
                return False, f"⏳ Вы заблокированы на {remaining} сек"
            
            # Очищаем старые записи
            cutoff = now - limit.period_seconds
            history.timestamps = [t for t in history.timestamps if t > cutoff]
            
            # Проверяем кулдаун
            if limit.cooldown_seconds > 0 and history.timestamps:
                last_action = history.timestamps[-1]
                time_since = now - last_action
                if time_since < limit.cooldown_seconds:
                    remaining = int(limit.cooldown_seconds - time_since)
                    return False, f"⏳ Подождите {remaining} сек"
            
            # Проверяем лимит
            if len(history.timestamps) >= limit.max_actions:
                # Блокируем пользователя
                history.blocked_until = now + limit.block_duration
                history.violations += 1
                
                # Логируем нарушение
                await self._log_violation(user_id, action_type, history.violations)
                
                return False, f"⚠️ Превышен лимит! Блокировка на {limit.block_duration} сек"
            
            # Предупреждение при приближении к лимиту
            usage_ratio = len(history.timestamps) / limit.max_actions
            if usage_ratio >= limit.warn_threshold and history.last_warning < cutoff:
                history.last_warning = now
                # Возвращаем разрешение, но с предупреждением
                return True, f"⚠️ Внимание: скоро будет достигнут лимит действий"
            
            return True, None
    
    async def record_action(self, user_id: int, action_type: ActionType):
        """Записать выполнение действия"""
        async with self._lock:
            key = (user_id, action_type)
            history = self._history.get(key)
            
            if history is None:
                history = UserActionHistory(
                    user_id=user_id,
                    action_type=action_type
                )
                self._history[key] = history
            
            history.timestamps.append(time.time())
    
    async def get_user_status(self, user_id: int) -> Dict:
        """Получить статус лимитов пользователя"""
        async with self._lock:
            now = time.time()
            status = {}
            
            for action_type in ActionType:
                key = (user_id, action_type)
                history = self._history.get(key)
                limit = self.get_limit(action_type)
                
                if not limit:
                    continue
                
                if history:
                    # Очищаем старые
                    cutoff = now - limit.period_seconds
                    current = len([t for t in history.timestamps if t > cutoff])
                    blocked = history.blocked_until > now
                else:
                    current = 0
                    blocked = False
                
                status[action_type.value] = {
                    "current": current,
                    "max": limit.max_actions,
                    "period": limit.period_seconds,
                    "blocked": blocked,
                    "violations": history.violations if history else 0
                }
            
            return status
    
    async def reset_user(self, user_id: int, action_type: ActionType = None):
        """Сбросить лимиты пользователя"""
        async with self._lock:
            if action_type:
                key = (user_id, action_type)
                if key in self._history:
                    del self._history[key]
            else:
                # Сбросить все лимиты пользователя
                keys_to_delete = [k for k in self._history if k[0] == user_id]
                for key in keys_to_delete:
                    del self._history[key]
    
    async def cleanup_old_records(self, max_age_hours: int = 24):
        """Очистка старых записей"""
        async with self._lock:
            cutoff = time.time() - (max_age_hours * 3600)
            
            keys_to_delete = []
            for key, history in self._history.items():
                # Удаляем если все записи старые и нет блокировки
                if (not history.timestamps or history.timestamps[-1] < cutoff) \
                   and history.blocked_until < cutoff:
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self._history[key]
            
            return len(keys_to_delete)
    
    async def _log_violation(self, user_id: int, action_type: ActionType, count: int):
        """Логирование нарушения"""
        import logging
        logger = logging.getLogger("rate_limiter")
        logger.warning(
            f"Rate limit violation | User: {user_id} | "
            f"Action: {action_type.value} | Violations: {count}"
        )


class AntiSpamMiddleware:
    """Middleware для защиты от спама"""
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
    
    async def check_callback(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """Проверка callback query"""
        return await self.rate_limiter.check_action(user_id, ActionType.CALLBACK)
    
    async def check_message(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """Проверка сообщения"""
        return await self.rate_limiter.check_action(user_id, ActionType.MESSAGE)
    
    async def check_click(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """Проверка клика"""
        return await self.rate_limiter.check_action(user_id, ActionType.CLICK)


class ClickSpeedProtector:
    """
    Защита от быстрых кликов (ботов).
    Анализирует скорость кликов и блокирует подозрительную активность.
    """
    
    # Минимальный интервал между кликами (секунды)
    MIN_CLICK_INTERVAL = 0.3  # 300 мс
    
    # Пороговые значения для определения бота
    BOT_THRESHOLDS = {
        "ultra_fast": 0.05,    # < 50 мс - точно бот
        "very_fast": 0.15,     # < 150 мс - вероятно бот
        "fast": 0.3,           # < 300 мс - подозрительно
    }
    
    def __init__(self):
        self._click_times: Dict[int, List[float]] = defaultdict(list)
        self._warnings: Dict[int, int] = defaultdict(int)
        self._blocked: Dict[int, float] = {}
        self._lock = asyncio.Lock()
    
    async def check_click(self, user_id: int) -> Tuple[bool, str, Optional[float]]:
        """
        Проверить клик на скорость.
        
        Returns:
            (allowed, status, speed)
            status: "ok", "warning", "blocked"
        """
        async with self._lock:
            now = time.time()
            
            # Проверяем блокировку
            if user_id in self._blocked:
                if self._blocked[user_id] > now:
                    remaining = self._blocked[user_id] - now
                    return False, "blocked", remaining
                else:
                    del self._blocked[user_id]
            
            # Получаем историю кликов
            times = self._click_times[user_id]
            
            # Оставляем только последние 100 кликов за минуту
            cutoff = now - 60
            times[:] = [t for t in times if t > cutoff]
            
            # Проверяем скорость
            if times:
                last_click = times[-1]
                interval = now - last_click
                
                # Анализируем интервал
                if interval < self.BOT_THRESHOLDS["ultra_fast"]:
                    # Точно бот - блокируем надолго
                    self._warnings[user_id] += 5
                    self._blocked[user_id] = now + 300  # 5 минут
                    return False, "blocked", interval
                
                elif interval < self.BOT_THRESHOLDS["very_fast"]:
                    # Вероятно бот
                    self._warnings[user_id] += 3
                    if self._warnings[user_id] >= 10:
                        self._blocked[user_id] = now + 120  # 2 минуты
                        return False, "blocked", interval
                    return True, "warning", interval
                
                elif interval < self.BOT_THRESHOLDS["fast"]:
                    # Подозрительно
                    self._warnings[user_id] += 1
                    if self._warnings[user_id] >= 20:
                        self._blocked[user_id] = now + 60  # 1 минута
                        return False, "blocked", interval
            
            # Записываем клик
            times.append(now)
            
            # Снижаем предупреждения за нормальные клики
            if self._warnings[user_id] > 0 and len(times) % 10 == 0:
                self._warnings[user_id] -= 1
            
            return True, "ok", None
    
    async def get_user_stats(self, user_id: int) -> Dict:
        """Статистика кликов пользователя"""
        async with self._lock:
            now = time.time()
            times = self._click_times.get(user_id, [])
            
            # Количество кликов за последнюю минуту
            recent = [t for t in times if t > now - 60]
            
            # Средний интервал
            if len(recent) >= 2:
                intervals = [recent[i] - recent[i-1] for i in range(1, len(recent))]
                avg_interval = sum(intervals) / len(intervals)
            else:
                avg_interval = 0
            
            return {
                "clicks_last_minute": len(recent),
                "avg_interval": round(avg_interval, 3),
                "warnings": self._warnings.get(user_id, 0),
                "is_blocked": user_id in self._blocked and self._blocked[user_id] > now
            }


# Глобальные экземпляры
rate_limiter = RateLimiter()
anti_spam = AntiSpamMiddleware(rate_limiter)
click_protector = ClickSpeedProtector()
