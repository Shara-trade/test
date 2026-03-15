"""
Декораторы для проверки прав администратора
Обновлено для новой архитектуры (пункт 1 ТЗ)
"""
from functools import wraps
from typing import Optional, Callable
from aiogram.types import CallbackQuery, Message
from aiogram.filters import BaseFilter

from .repositories import AdminRepository
from config import DATABASE_PATH

# Глобальный репозиторий
_repo = None


def _get_repo() -> AdminRepository:
    """Получить экземпляр репозитория"""
    global _repo
    if _repo is None:
        _repo = AdminRepository(DATABASE_PATH)
    return _repo


async def is_admin(user_id: int) -> bool:
    """Проверка прав админа"""
    repo = _get_repo()
    return await repo.is_admin(user_id)


async def check_permission(user_id: int, permission: str) -> bool:
    """Проверка права доступа"""
    from .services import get_admin_service
    
    service = get_admin_service(DATABASE_PATH)
    return await service.check_permission(user_id, permission)


async def get_admin_role(user_id: int) -> Optional[str]:
    """Получить роль админа"""
    repo = _get_repo()
    return await repo.get_admin_role(user_id)


def admin_required(permission: str = None):
    """
    Декоратор для проверки прав администратора.
    
    Args:
        permission: Необходимое право (players, economy, settings, etc.)
                   Если None — проверяется только наличие прав админа
    
    Usage:
        @admin_required("players")
        async def my_handler(callback: CallbackQuery):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(event, *args, **kwargs):
            # Получаем user_id в зависимости от типа события
            if isinstance(event, CallbackQuery):
                user_id = event.from_user.id
            elif isinstance(event, Message):
                user_id = event.from_user.id
            else:
                # Пытаемся получить из атрибута
                user_id = getattr(event, 'from_user', None)
                if user_id:
                    user_id = user_id.id
                else:
                    return await func(event, *args, **kwargs)
            
            # Проверяем, что пользователь — админ
            if not await is_admin(user_id):
                if isinstance(event, CallbackQuery):
                    await event.answer("⛔ Нет доступа", show_alert=True)
                elif isinstance(event, Message):
                    await event.answer("⛔ У вас нет доступа к этой команде")
                return
            
            # Если указано конкретное право — проверяем его
            if permission and not await check_permission(user_id, permission):
                if isinstance(event, CallbackQuery):
                    await event.answer(f"⛔ Недостаточно прав (требуется: {permission})", show_alert=True)
                elif isinstance(event, Message):
                    await event.answer(f"⛔ Недостаточно прав. Требуется право: {permission}")
                return
            
            # Всё ок — вызываем функцию
            return await func(event, *args, **kwargs)
        
        return wrapper
    return decorator


class AdminFilter(BaseFilter):
    """
    Фильтр для проверки прав администратора.
    Можно использовать в router.message() и router.callback_query()
    
    Usage:
        @router.callback_query(AdminFilter())
        async def admin_handler(callback: CallbackQuery):
            ...
        
        @router.callback_query(AdminFilter(permission="players"))
        async def players_handler(callback: CallbackQuery):
            ...
    """
    
    def __init__(self, permission: str = None):
        self.permission = permission
    
    async def __call__(self, event) -> bool:
        # Получаем user_id
        if isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        elif isinstance(event, Message):
            user_id = event.from_user.id
        else:
            return False
        
        # Проверяем админа
        if not await is_admin(user_id):
            return False
        
        # Проверяем право если указано
        if self.permission:
            return await check_permission(user_id, self.permission)
        
        return True


async def require_admin(user_id: int, permission: str = None) -> tuple:
    """
    Проверить права администратора и вернуть результат.
    
    Args:
        user_id: ID пользователя
        permission: Требуемое право (опционально)
    
    Returns:
        (has_access, error_message)
    """
    if not await is_admin(user_id):
        return False, "⛔ У вас нет доступа к админ-панели"
    
    if permission and not await check_permission(user_id, permission):
        return False, f"⛔ Недостаточно прав. Требуется: {permission}"
    
    return True, None
