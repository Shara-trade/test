"""
Пункт5. АДМИН-ПАНЕЛЬ
Пакет для управления ботом

Новая архитектура (пункт 1 ТЗ):
- repositories.py - работа с БД
- services.py - бизнес-логика
- schemas.py - валидация (Pydantic)
- handlers.py - обработчики (в handlers/admin_panel.py)
- keyboards.py - клавиатуры

Примечание: router находится в handlers/admin_panel.py
"""

from .permissions import PermissionManager, Permission
from .broadcast import BroadcastSystem
from .balance import BalanceManager
from .settings import AdminSettingsManager, RARITY_PRESETS

# Новая архитектура
from .repositories import AdminRepository
from .services import (
    AdminService, AdminCacheService, ConfirmationService,
    get_admin_service, get_cache_service, get_confirmation_service
)
from .schemas import (
    ResourceType, ContainerType, ModuleRarity, BanDuration,
    ResourceUpdateSchema, ResourceSingleUpdateSchema,
    GiveContainerSchema, GiveMaterialSchema, GiveModuleSchema,
    BanPlayerSchema, PlayerSearchSchema, PlayerCardSchema,
    SuccessResponse, ErrorResponse
)

__all__ = [
    # Старые (для совместимости)
    'PermissionManager',
    'Permission',
    'BroadcastSystem',
    'BalanceManager',
    'AdminSettingsManager',
    'RARITY_PRESETS',
    
    # Новые
    'AdminRepository',
    'AdminService',
    'AdminCacheService',
    'ConfirmationService',
    'get_admin_service',
    'get_cache_service',
    'get_confirmation_service',
    
    # Схемы
    'ResourceType',
    'ContainerType',
    'ModuleRarity',
    'BanDuration',
    'ResourceUpdateSchema',
    'ResourceSingleUpdateSchema',
    'GiveContainerSchema',
    'GiveMaterialSchema',
    'GiveModuleSchema',
    'BanPlayerSchema',
    'PlayerSearchSchema',
    'PlayerCardSchema',
    'SuccessResponse',
    'ErrorResponse',
]
