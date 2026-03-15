"""
Middleware для админ-панели
Rate Limiting и защита от массовых операций
"""
import time
from typing import Dict, List
from collections import defaultdict
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message


class AdminRateLimitMiddleware(BaseMiddleware):
    """
    Middleware для ограничения частоты админских действий.
    Защищает от случайных или намеренных массовых операций.
    """
    
    # Лимиты по типам действий
    RATE_LIMITS = {
        # Действия с игроками
        "edit_resource": {"max": 50, "window": 3600},      # 50 изменений ресурсов в час
        "give_item": {"max": 100, "window": 3600},         # 100 выдач предметов в час
        "give_container": {"max": 50, "window": 3600},      # 50 выдач контейнеров в час
        "give_module": {"max": 30, "window": 3600},         # 30 выдач модулей в час
        "give_material": {"max": 100, "window": 3600},      # 100 выдач материалов в час
        
        # Критичные действия
        "ban_player": {"max": 20, "window": 3600},          # 20 банов в час
        "unban_player": {"max": 20, "window": 3600},        # 20 разбанов в час
        "reset_player": {"max": 5, "window": 3600},         # 5 сбросов в час
        
        # Массовые операции
        "mass_operation": {"max": 3, "window": 3600},       # 3 массовые операции в час
        
        # Настройки
        "edit_setting": {"max": 30, "window": 3600},        # 30 изменений настроек в час
        
        # Общие админ-действия
        "default": {"max": 100, "window": 3600},            # По умолчанию 100 в час
    }
    
    # Публичные админ-действия (без ограничений)
    UNLIMITED_ACTIONS = {
        "main", "close", "stats", "logs", "players:find", 
        "players:card", "modules:stats", "containers:stats"
    }
    
    def __init__(self):
        # Хранилище: {user_id: {action: [timestamp1, timestamp2, ...]}}
        self._requests: Dict[int, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        
        # Время последней очистки
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # Очистка каждые 5 минут
    
    def _get_action_type(self, callback_data: str) -> str:
        """
        Определить тип действия из callback_data.
        
        Args:
            callback_data: Данные callback
            
        Returns:
            str - тип действия
        """
        if not callback_data.startswith("admin:"):
            return "default"
        
        parts = callback_data.split(":")
        
        # Проверяем публичные действия
        if len(parts) >= 2:
            action_key = ":".join(parts[1:3]) if len(parts) > 2 else parts[1]
            if action_key in self.UNLIMITED_ACTIONS or parts[1] in self.UNLIMITED_ACTIONS:
                return "unlimited"
        
        # Определяем тип действия
        if "confirm" in callback_data:
            # Это подтверждение, не считаем отдельно
            return "unlimited"
        
        if "edit_resource" in callback_data or ":res:" in callback_data:
            return "edit_resource"
        
        if "give_container" in callback_data:
            return "give_container"
        
        if "give_module" in callback_data:
            return "give_module"
        
        if "give_material" in callback_data:
            return "give_material"
        
        if "ban" in callback_data:
            return "ban_player"
        
        if "unban" in callback_data:
            return "unban_player"
        
        if "reset" in callback_data:
            return "reset_player"
        
        if "mass" in callback_data:
            return "mass_operation"
        
        if "settings" in callback_data:
            return "edit_setting"
        
        return "default"
    
    def _cleanup_old_requests(self):
        """Очистка старых записей"""
        now = time.time()
        
        if now - self._last_cleanup < self._cleanup_interval:
            return
        
        # Удаляем записи старше максимального окна (1 час)
        max_window = 3600
        
        for user_id in list(self._requests.keys()):
            for action in list(self._requests[user_id].keys()):
                # Фильтруем старые запросы
                self._requests[user_id][action] = [
                    ts for ts in self._requests[user_id][action]
                    if now - ts < max_window
                ]
                
                # Удаляем пустые списки
                if not self._requests[user_id][action]:
                    del self._requests[user_id][action]
            
            # Удаляем пустых пользователей
            if not self._requests[user_id]:
                del self._requests[user_id]
        
        self._last_cleanup = now
    
    def _check_rate_limit(self, user_id: int, action: str) -> tuple:
        """
        Проверить лимит частоты для действия.
        
        Args:
            user_id: ID пользователя
            action: Тип действия
            
        Returns:
            (is_allowed, remaining, reset_time)
        """
        if action == "unlimited":
            return True, 0, 0
        
        now = time.time()
        
        # Получаем лимиты для действия
        limits = self.RATE_LIMITS.get(action, self.RATE_LIMITS["default"])
        max_requests = limits["max"]
        window = limits["window"]
        
        # Получаем список запросов пользователя
        requests = self._requests[user_id][action]
        
        # Фильтруем запросы в рамках окна
        requests_in_window = [ts for ts in requests if now - ts < window]
        
        # Проверяем лимит
        if len(requests_in_window) >= max_requests:
            # Лимит превышен
            oldest_request = min(requests_in_window)
            reset_time = int(window - (now - oldest_request))
            remaining = 0
            
            return False, remaining, reset_time
        
        # Добавляем текущий запрос
        requests_in_window.append(now)
        self._requests[user_id][action] = requests_in_window
        
        remaining = max_requests - len(requests_in_window)
        
        return True, remaining, 0
    
    async def __call__(self, handler, event, data):
        """Обработка события"""
        
        # Очистка старых записей
        self._cleanup_old_requests()
        
        if isinstance(event, CallbackQuery):
            callback_data = event.data
            
            # Проверяем только админские callback
            if not callback_data or not callback_data.startswith("admin:"):
                return await handler(event, data)
            
            user_id = event.from_user.id
            
            # Определяем тип действия
            action = self._get_action_type(callback_data)
            
            # Проверяем лимит
            is_allowed, remaining, reset_time = self._check_rate_limit(user_id, action)
            
            if not is_allowed:
                # Формируем сообщение об ошибке
                if reset_time > 60:
                    time_str = f"{reset_time // 60} мин."
                else:
                    time_str = f"{reset_time} сек."
                
                await event.answer(
                    f"⚠️ Слишком много действий. Подождите {time_str}",
                    show_alert=True
                )
                return
        
        return await handler(event, data)


class AdminAuditMiddleware(BaseMiddleware):
    """
    Middleware для аудита всех админских действий.
    Записывает все callback и команды админов.
    """
    
    # Действия, которые не нужно логировать
    SKIP_ACTIONS = {
        "admin:main",
        "admin:close",
        "admin:players:find",
        "admin:stats",
        "admin:logs",
    }
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    async def __call__(self, handler, event, data):
        """Обработка события"""
        
        if isinstance(event, CallbackQuery):
            callback_data = event.data
            
            if not callback_data or not callback_data.startswith("admin:"):
                return await handler(event, data)
            
            # Пропускаем незначимые действия
            if callback_data in self.SKIP_ACTIONS:
                return await handler(event, data)
            
            user_id = event.from_user.id
            
            # Проверяем, что это админ
            from .repositories import AdminRepository
            repo = AdminRepository(self.db_path)
            
            if not await repo.is_admin(user_id):
                return await handler(event, data)
            
            # Выполняем обработчик
            result = await handler(event, data)
            
            # Логируем действие
            await self._log_action(user_id, callback_data, event)
            
            return result
        
        return await handler(event, data)
    
    async def _log_action(self, admin_id: int, action: str, event: CallbackQuery):
        """Записать действие в лог"""
        try:
            from .repositories import AdminRepository
            
            repo = AdminRepository(self.db_path)
            
            # Извлекаем целевого пользователя из callback_data
            target_user_id = None
            parts = action.split(":")
            
            # Ищем число в callback_data (обычно это user_id)
            for part in parts:
                if part.isdigit():
                    target_user_id = int(part)
                    break
            
            # Определяем тип действия
            action_type = self._get_action_type(action)
            
            # Записываем в лог
            await repo.log_action(
                admin_id=admin_id,
                action=action_type,
                target_user_id=target_user_id,
                details=action
            )
            
        except Exception as e:
            print(f"Error logging admin action: {e}")
    
    def _get_action_type(self, callback_data: str) -> str:
        """Определить тип действия для логирования"""
        
        if "edit_resource" in callback_data or ":res:" in callback_data:
            return "edit_resource"
        elif "give_container" in callback_data:
            return "give_container"
        elif "give_module" in callback_data:
            return "give_module"
        elif "give_material" in callback_data:
            return "give_material"
        elif "ban" in callback_data:
            return "ban_player"
        elif "unban" in callback_data:
            return "unban_player"
        elif "reset" in callback_data:
            return "reset_player"
        elif "mass" in callback_data:
            return "mass_operation"
        elif "settings" in callback_data:
            return "edit_setting"
        else:
            return "admin_action"


# Глобальные экземпляры
_rate_limit_middleware = None
_audit_middleware = None


def get_rate_limit_middleware() -> AdminRateLimitMiddleware:
    """Получить экземпляр Rate Limit middleware"""
    global _rate_limit_middleware
    if _rate_limit_middleware is None:
        _rate_limit_middleware = AdminRateLimitMiddleware()
    return _rate_limit_middleware


def get_audit_middleware(db_path: str) -> AdminAuditMiddleware:
    """Получить экземпляр Audit middleware"""
    global _audit_middleware
    if _audit_middleware is None:
        _audit_middleware = AdminAuditMiddleware(db_path)
    return _audit_middleware
