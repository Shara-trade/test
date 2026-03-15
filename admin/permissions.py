"""
5.1. Доступ и верификация
Система прав админов
"""
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class Permission(Enum):
    """Права доступа"""
    # Базовые права
    VIEW_STATS = "view_stats"           # Просмотр статистики
    VIEW_LOGS = "view_logs"             # Просмотр логов
    
    # Управление игроками
    MANAGE_PLAYERS = "manage_players"   # Управление игроками
    BAN_PLAYERS = "ban_players"         # Бан игроков
    GIVE_ITEMS = "give_items"           # Выдача предметов
    GIVE_RESOURCES = "give_resources"   # Выдача ресурсов
    
    # Управление контентом
    MANAGE_ITEMS = "manage_items"       # Управление предметами
    MANAGE_DRONES = "manage_drones"     # Управление дронами
    MANAGE_MARKET = "manage_market"     # Управление рынком
    MANAGE_CLANS = "manage_clans"       # Управление кланами
    
    # Ивенты и рассылки
    MANAGE_EVENTS = "manage_events"     # Управление ивентами
    BROADCAST = "broadcast"             # Рассылка сообщений
    
    # Балансировка
    BALANCE = "balance"                 # Балансировка игры
    
    # Супер-админ
    SUPER_ADMIN = "super_admin"         # Все права + управление админами


# Уровни админов с предустановленными правами
ADMIN_LEVELS = {
    1: [  # Модератор
        Permission.VIEW_STATS,
        Permission.VIEW_LOGS,
        Permission.MANAGE_PLAYERS,
    ],
    2: [  # Старший модератор
        Permission.VIEW_STATS,
        Permission.VIEW_LOGS,
        Permission.MANAGE_PLAYERS,
        Permission.BAN_PLAYERS,
        Permission.GIVE_ITEMS,
        Permission.GIVE_RESOURCES,
    ],
    3: [  # Администратор
        Permission.VIEW_STATS,
        Permission.VIEW_LOGS,
        Permission.MANAGE_PLAYERS,
        Permission.BAN_PLAYERS,
        Permission.GIVE_ITEMS,
        Permission.GIVE_RESOURCES,
        Permission.MANAGE_ITEMS,
        Permission.MANAGE_DRONES,
        Permission.MANAGE_MARKET,
        Permission.MANAGE_CLANS,
        Permission.MANAGE_EVENTS,
        Permission.BROADCAST,
    ],
    4: [  # Главный администратор
        Permission.VIEW_STATS,
        Permission.VIEW_LOGS,
        Permission.MANAGE_PLAYERS,
        Permission.BAN_PLAYERS,
        Permission.GIVE_ITEMS,
        Permission.GIVE_RESOURCES,
        Permission.MANAGE_ITEMS,
        Permission.MANAGE_DRONES,
        Permission.MANAGE_MARKET,
        Permission.MANAGE_CLANS,
        Permission.MANAGE_EVENTS,
        Permission.BROADCAST,
        Permission.BALANCE,
    ],
    5: [  # Супер-админ (все права)
        Permission.SUPER_ADMIN,
    ],
}


@dataclass
class AdminUser:
    """Модель админа"""
    user_id: int
    username: Optional[str]
    level: int = 1
    permissions: List[Permission] = None
    added_by: Optional[int] = None
    added_at: Optional[str] = None
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = ADMIN_LEVELS.get(self.level, [])
    
    def has_permission(self, permission: Permission) -> bool:
        """Проверка права"""
        if Permission.SUPER_ADMIN in self.permissions:
            return True
        return permission in self.permissions
    
    def add_permission(self, permission: Permission):
        """Добавить право"""
        if permission not in self.permissions:
            self.permissions.append(permission)
    
    def remove_permission(self, permission: Permission):
        """Убрать право"""
        if permission in self.permissions and permission != Permission.SUPER_ADMIN:
            self.permissions.remove(permission)


class PermissionManager:
    """Менеджер прав доступа"""
    
    # Список супер-админов (из конфига)
    SUPER_ADMINS = []
    
    @classmethod
    def is_admin(cls, user_id: int, admin_list: dict) -> bool:
        """Проверка, является ли пользователь админом"""
        return user_id in admin_list or user_id in cls.SUPER_ADMINS
    
    @classmethod
    def is_super_admin(cls, user_id: int) -> bool:
        """Проверка супер-админа"""
        return user_id in cls.SUPER_ADMINS
    
    @classmethod
    def get_admin_level(cls, user_id: int, admin_list: dict) -> int:
        """Получить уровень админа"""
        if user_id in cls.SUPER_ADMINS:
            return 5
        if user_id in admin_list:
            return admin_list[user_id].get("level", 1)
        return 0
    
    @classmethod
    def check_permission(cls, user_id: int, permission: Permission, 
                         admin_list: dict) -> bool:
        """Проверка права доступа"""
        if user_id in cls.SUPER_ADMINS:
            return True
        
        if user_id not in admin_list:
            return False
        
        admin_data = admin_list[user_id]
        level = admin_data.get("level", 1)
        permissions = admin_data.get("permissions", [])
        
        # Проверка по уровню
        level_permissions = ADMIN_LEVELS.get(level, [])
        if permission in level_permissions:
            return True
        
        # Проверка кастомных прав
        permission_str = permission.value if isinstance(permission, Permission) else permission
        return permission_str in permissions
    
    @classmethod
    def get_permissions_by_level(cls, level: int) -> List[Permission]:
        """Получить права по уровню"""
        return ADMIN_LEVELS.get(level, [])
    
    @classmethod
    def format_permissions(cls, permissions: List[Permission]) -> str:
        """Форматировать список прав для отображения"""
        if not permissions:
            return "Нет прав"
        
        names = {
            Permission.VIEW_STATS: "📊 Статистика",
            Permission.VIEW_LOGS: "📜 Логи",
            Permission.MANAGE_PLAYERS: "👥 Игроки",
            Permission.BAN_PLAYERS: "🚫 Бан",
            Permission.GIVE_ITEMS: "📦 Выдача предметов",
            Permission.GIVE_RESOURCES: "💰 Выдача ресурсов",
            Permission.MANAGE_ITEMS: "⚙️ Предметы",
            Permission.MANAGE_DRONES: "🤖 Дроны",
            Permission.MANAGE_MARKET: "🏪 Рынок",
            Permission.MANAGE_CLANS: "👥 Кланы",
            Permission.MANAGE_EVENTS: "🎯 Ивенты",
            Permission.BROADCAST: "📢 Рассылка",
            Permission.BALANCE: "⚖️ Баланс",
            Permission.SUPER_ADMIN: "👑 Супер-админ",
        }
        
        return "\n".join(f"✅ {names.get(p, p.value)}" for p in permissions)
