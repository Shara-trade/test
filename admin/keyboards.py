"""
Клавиатуры админ-панели
Согласно Admin_panel.txt
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Optional, List, Dict


# ===== ГЛАВНОЕ МЕНЮ =====

def get_admin_main_keyboard(role: str = "support") -> InlineKeyboardMarkup:
    """Главное меню админ-панели"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="👤 Игроки", callback_data="admin:players"),
        InlineKeyboardButton(text="📦 Контейнеры", callback_data="admin:containers")
    )
    builder.row(
        InlineKeyboardButton(text="🧩 Модули", callback_data="admin:modules"),
        InlineKeyboardButton(text="🎲 Дроп", callback_data="admin:drop")
    )
    builder.row(
        InlineKeyboardButton(text="💰 Экономика", callback_data="admin:economy"),
        InlineKeyboardButton(text="🧱 Материалы", callback_data="admin:materials")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats"),
        InlineKeyboardButton(text="📜 Логи", callback_data="admin:logs")
    )
    builder.row(
        InlineKeyboardButton(text="🧪 Тестирование", callback_data="admin:testing"),
        InlineKeyboardButton(text="🎉 События", callback_data="admin:events")
    )
    builder.row(
        InlineKeyboardButton(text="💾 Бэкапы", callback_data="admin:backups"),
        InlineKeyboardButton(text="📈 Метрики", callback_data="admin:metrics")
    )
    builder.row(
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin:settings")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Закрыть панель", callback_data="admin:close")
    )
    
    return builder.as_markup()


# ===== МЕНЮ ИГРОКОВ =====

def get_players_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню управления игроками"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🔍 Найти игрока", callback_data="admin:players:find")
    )
    builder.row(
        InlineKeyboardButton(text="💰 Изменить ресурсы", callback_data="admin:players:resources"),
        InlineKeyboardButton(text="📦 Выдать контейнер", callback_data="admin:players:give_container")
    )
    builder.row(
        InlineKeyboardButton(text="🧩 Выдать модуль", callback_data="admin:players:give_module"),
        InlineKeyboardButton(text="🧱 Выдать материал", callback_data="admin:players:give_material")
    )
    builder.row(
        InlineKeyboardButton(text="🚫 Бан игрока", callback_data="admin:players:ban"),
        InlineKeyboardButton(text="♻️ Сброс игрока", callback_data="admin:players:reset")
    )
    builder.row(
        InlineKeyboardButton(text="👥 Массовые операции", callback_data="admin:players:mass")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:main"),
        InlineKeyboardButton(text="❌ Закрыть", callback_data="admin:close")
    )
    
    return builder.as_markup()


def get_player_card_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Карточка игрока"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="💰 Изменить ресурсы", callback_data=f"admin:players:resources:{user_id}")
    )
    builder.row(
        InlineKeyboardButton(text="📦 Выдать контейнер", callback_data=f"admin:players:give_container:{user_id}"),
        InlineKeyboardButton(text="🧩 Выдать модуль", callback_data=f"admin:players:give_module:{user_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🧱 Выдать материал", callback_data=f"admin:players:give_material:{user_id}"),
        InlineKeyboardButton(text="🚫 Бан игрока", callback_data=f"admin:players:ban:{user_id}")
    )
    builder.row(
        InlineKeyboardButton(text="📜 История", callback_data=f"admin:players:history:{user_id}")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:players"),
        InlineKeyboardButton(text="❌ Закрыть", callback_data="admin:close")
    )
    
    return builder.as_markup()


def get_resource_select_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Выбор ресурса для изменения"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="⚙️ Металл", callback_data=f"admin:players:res:{user_id}:metal"),
        InlineKeyboardButton(text="💎 Кристаллы", callback_data=f"admin:players:res:{user_id}:crystals")
    )
    builder.row(
        InlineKeyboardButton(text="🕳️ Тёмная материя", callback_data=f"admin:players:res:{user_id}:dark_matter")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin:players:card:{user_id}")
    )
    
    return builder.as_markup()


def get_container_type_keyboard(action: str = "give", target_id: int = None) -> InlineKeyboardMarkup:
    """Выбор типа контейнера"""
    builder = InlineKeyboardBuilder()
    
    prefix = f"admin:{action}" if not target_id else f"admin:players:{action}:{target_id}"
    
    builder.row(
        InlineKeyboardButton(text="📦 Обычный", callback_data=f"{prefix}:container:common"),
        InlineKeyboardButton(text="🎁 Редкий", callback_data=f"{prefix}:container:rare")
    )
    builder.row(
        InlineKeyboardButton(text="💎 Эпический", callback_data=f"{prefix}:container:epic"),
        InlineKeyboardButton(text="👑 Мифический", callback_data=f"{prefix}:container:mythic")
    )
    builder.row(
        InlineKeyboardButton(text="🔥 Легендарный", callback_data=f"{prefix}:container:legendary"),
        InlineKeyboardButton(text="🧰 КСМ", callback_data=f"{prefix}:container:ksm")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:players" if not target_id else f"admin:players:card:{target_id}")
    )
    
    return builder.as_markup()


def get_module_rarity_keyboard(action: str = "give", target_id: int = None) -> InlineKeyboardMarkup:
    """Выбор редкости модуля"""
    builder = InlineKeyboardBuilder()
    
    prefix = f"admin:{action}" if not target_id else f"admin:players:{action}:{target_id}"
    
    builder.row(
        InlineKeyboardButton(text="⚪️ Обычный", callback_data=f"{prefix}:module:common"),
        InlineKeyboardButton(text="🟢 Редкий", callback_data=f"{prefix}:module:rare")
    )
    builder.row(
        InlineKeyboardButton(text="🟣 Эпический", callback_data=f"{prefix}:module:epic"),
        InlineKeyboardButton(text="🔴 Мифический", callback_data=f"{prefix}:module:mythic")
    )
    builder.row(
        InlineKeyboardButton(text="🟡 Легендарный", callback_data=f"{prefix}:module:legendary")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:players" if not target_id else f"admin:players:card:{target_id}")
    )
    
    return builder.as_markup()


def get_materials_keyboard(page: int = 1, action: str = "give", target_id: int = None) -> InlineKeyboardMarkup:
    """Выбор материала с пагинацией"""
    from game.materials import MaterialSystem
    
    materials = MaterialSystem.get_all_materials()
    per_page = 5
    total_pages = (len(materials) + per_page - 1) // per_page
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_materials = materials[start_idx:end_idx]
    
    builder = InlineKeyboardBuilder()
    
    prefix = f"admin:players:{action}:{target_id}" if target_id else f"admin:materials"
    
    for mat in page_materials:
        builder.row(
            InlineKeyboardButton(
                text=f"{mat.emoji} {mat.name}",
                callback_data=f"{prefix}:material:{mat.key}"
            )
        )
    
    # Пагинация
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="«", callback_data=f"admin:materials:page:{page-1}"))
    nav_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="admin:materials:page:info"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="»", callback_data=f"admin:materials:page:{page+1}"))
    
    if len(nav_buttons) > 1:
        builder.row(*nav_buttons)
    
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:players" if not target_id else f"admin:players:card:{target_id}")
    )
    
    return builder.as_markup()


def get_ban_duration_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Выбор срока бана"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="⏱️ 1 час", callback_data=f"admin:players:ban:{user_id}:1h"),
        InlineKeyboardButton(text="⏱️ 24 часа", callback_data=f"admin:players:ban:{user_id}:24h")
    )
    builder.row(
        InlineKeyboardButton(text="⏱️ 7 дней", callback_data=f"admin:players:ban:{user_id}:7d"),
        InlineKeyboardButton(text="⏱️ Навсегда", callback_data=f"admin:players:ban:{user_id}:forever")
    )
    builder.row(
        InlineKeyboardButton(text="✏️ Свой срок", callback_data=f"admin:players:ban:{user_id}:custom")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin:players:card:{user_id}")
    )
    
    return builder.as_markup()


def get_confirm_keyboard(confirm_data: str, cancel_data: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data=confirm_data),
        InlineKeyboardButton(text="⬅️ Отмена", callback_data=cancel_data)
    )
    
    return builder.as_markup()


def get_back_keyboard(back_data: str = "admin:main") -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой назад"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=back_data),
        InlineKeyboardButton(text="❌ Закрыть", callback_data="admin:close")
    )
    return builder.as_markup()


# ===== МЕНЮ КОНТЕЙНЕРОВ =====

def get_containers_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню управления контейнерами"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🎲 Шансы материалов", callback_data="admin:containers:material_chances"),
        InlineKeyboardButton(text="💰 Награды ресурсов", callback_data="admin:containers:rewards")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Статистика контейнеров", callback_data="admin:containers:stats")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:main"),
        InlineKeyboardButton(text="❌ Закрыть", callback_data="admin:close")
    )
    
    return builder.as_markup()


# ===== МЕНЮ МОДУЛЕЙ =====

def get_modules_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню управления модулями"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin:modules:stats"),
        InlineKeyboardButton(text="🧪 Генерация тестового", callback_data="admin:modules:test")
    )
    builder.row(
        InlineKeyboardButton(text="🔍 Поиск модулей", callback_data="admin:modules:search")
    )
    builder.row(
        InlineKeyboardButton(text="💚 Управление бафами", callback_data="admin:modules:buffs"),
        InlineKeyboardButton(text="❤️ Управление дебафами", callback_data="admin:modules:debuffs")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:main"),
        InlineKeyboardButton(text="❌ Закрыть", callback_data="admin:close")
    )
    
    return builder.as_markup()


def get_buffs_keyboard(page: int = 1) -> InlineKeyboardMarkup:
    """Список бафов с пагинацией"""
    from game.modules import BUFF_NAMES, BUFF_KEYS
    
    per_page = 5
    total_pages = (len(BUFF_KEYS) + per_page - 1) // per_page
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_buffs = BUFF_KEYS[start_idx:end_idx]
    
    builder = InlineKeyboardBuilder()
    
    for i, buff_key in enumerate(page_buffs, start=start_idx + 1):
        name = BUFF_NAMES.get(buff_key, buff_key)
        builder.row(
            InlineKeyboardButton(
                text=f"{i}. {name}",
                callback_data=f"admin:modules:buff:{buff_key}"
            ),
            InlineKeyboardButton(
                text="✏️",
                callback_data=f"admin:modules:buff:edit:{buff_key}"
            )
        )
    
    # Пагинация
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="«", callback_data=f"admin:modules:buffs:{page-1}"))
    nav_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="admin:modules:buffs:info"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="»", callback_data=f"admin:modules:buffs:{page+1}"))
    
    if len(nav_buttons) > 1:
        builder.row(*nav_buttons)
    
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:modules")
    )
    
    return builder.as_markup()


# ===== МЕНЮ ДРОПА =====

def get_drop_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню управления дропом"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🎲 Шансы редкости модулей", callback_data="admin:drop:rarity")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Пресеты", callback_data="admin:drop:presets")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:main"),
        InlineKeyboardButton(text="❌ Закрыть", callback_data="admin:close")
    )
    
    return builder.as_markup()


def get_rarity_presets_keyboard() -> InlineKeyboardMarkup:
    """Пресеты шансов редкости"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📊 Стандартный\n70/20/7/2.5/0.5", callback_data="admin:drop:preset:standard")
    )
    builder.row(
        InlineKeyboardButton(text="⚡ Быстрый\n50/30/15/4/1", callback_data="admin:drop:preset:fast")
    )
    builder.row(
        InlineKeyboardButton(text="🎁 Щедрый\n40/30/20/8/2", callback_data="admin:drop:preset:generous")
    )
    builder.row(
        InlineKeyboardButton(text="💎 Хардкорный\n85/10/4/0.9/0.1", callback_data="admin:drop:preset:hardcore")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:drop")
    )
    
    return builder.as_markup()


# ===== МЕНЮ ЭКОНОМИКИ =====

def get_economy_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню экономики"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="💰 Цена продажи модулей", callback_data="admin:economy:sell_prices"),
        InlineKeyboardButton(text="📦 Награды контейнеров", callback_data="admin:economy:container_rewards")
    )
    builder.row(
        InlineKeyboardButton(text="🔧 Стоимость улучшения", callback_data="admin:economy:upgrade_costs")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:main"),
        InlineKeyboardButton(text="❌ Закрыть", callback_data="admin:close")
    )
    
    return builder.as_markup()


# ===== МЕНЮ СТАТИСТИКИ =====

def get_stats_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню статистики"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📊 Детальная статистика", callback_data="admin:stats:detailed")
    )
    builder.row(
        InlineKeyboardButton(text="🔄 Обновить", callback_data="admin:stats:refresh")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:main"),
        InlineKeyboardButton(text="❌ Закрыть", callback_data="admin:close")
    )
    
    return builder.as_markup()


# ===== МЕНЮ ЛОГОВ =====

def get_logs_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню логов"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📜 Все действия", callback_data="admin:logs:all"),
        InlineKeyboardButton(text="🔍 Фильтр", callback_data="admin:logs:filter")
    )
    builder.row(
        InlineKeyboardButton(text="👤 По администратору", callback_data="admin:logs:by_admin"),
        InlineKeyboardButton(text="🎯 По действию", callback_data="admin:logs:by_action")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:main"),
        InlineKeyboardButton(text="❌ Закрыть", callback_data="admin:close")
    )
    
    return builder.as_markup()


def get_logs_pagination_keyboard(page: int, total_pages: int, filter_data: str = "") -> InlineKeyboardMarkup:
    """Пагинация логов"""
    builder = InlineKeyboardBuilder()
    
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="«", callback_data=f"admin:logs:page:{page-1}:{filter_data}"))
    nav_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="admin:logs:page:info"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="»", callback_data=f"admin:logs:page:{page+1}:{filter_data}"))
    
    if len(nav_buttons) > 1:
        builder.row(*nav_buttons)
    
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:logs"),
        InlineKeyboardButton(text="❌ Закрыть", callback_data="admin:close")
    )
    
    return builder.as_markup()


# ===== МЕНЮ ТЕСТИРОВАНИЯ =====

def get_testing_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню тестирования"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🧪 Тест генерации модуля", callback_data="admin:testing:module"),
        InlineKeyboardButton(text="📦 Тест контейнера", callback_data="admin:testing:container")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:main"),
        InlineKeyboardButton(text="❌ Закрыть", callback_data="admin:close")
    )
    
    return builder.as_markup()


# ===== МЕНЮ НАСТРОЕК =====

def get_settings_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню настроек"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🛡️ Антиспам", callback_data="admin:settings:antispam"),
        InlineKeyboardButton(text="📦 Лимиты выдачи", callback_data="admin:settings:limits")
    )
    builder.row(
        InlineKeyboardButton(text="👥 Управление админами", callback_data="admin:settings:admins"),
        InlineKeyboardButton(text="📨 Уведомления", callback_data="admin:settings:notifications")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:main"),
        InlineKeyboardButton(text="❌ Закрыть", callback_data="admin:close")
    )
    
    return builder.as_markup()


# ===== МЕНЮ СОБЫТИЙ =====

def get_events_menu_keyboard(has_active: bool = False) -> InlineKeyboardMarkup:
    """Меню событий"""
    builder = InlineKeyboardBuilder()
    
    if has_active:
        builder.row(
            InlineKeyboardButton(text="🎉 Активные ивенты", callback_data="admin:events:active")
        )
    
    builder.row(
        InlineKeyboardButton(text="➕ Создать ивент", callback_data="admin:events:create")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:main"),
        InlineKeyboardButton(text="❌ Закрыть", callback_data="admin:close")
    )
    
    return builder.as_markup()


def get_event_type_keyboard() -> InlineKeyboardMarkup:
    """Выбор типа ивента"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📦 Удвоенный дроп из контейнеров", callback_data="admin:events:create:container_drop")
    )
    builder.row(
        InlineKeyboardButton(text="💰 Скидка на улучшение модулей", callback_data="admin:events:create:upgrade_discount")
    )
    builder.row(
        InlineKeyboardButton(text="🎁 Бонусные контейнеры за активность", callback_data="admin:events:create:bonus_containers")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:events")
    )
    
    return builder.as_markup()


# ===== МЕНЮ БЭКАПОВ =====

def get_backups_menu_keyboard(has_backups: bool = False) -> InlineKeyboardMarkup:
    """Меню бэкапов"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📀 Создать бэкап", callback_data="admin:backups:create")
    )
    
    if has_backups:
        builder.row(
            InlineKeyboardButton(text="📋 Список бэкапов", callback_data="admin:backups:list"),
            InlineKeyboardButton(text="📂 Восстановить", callback_data="admin:backups:restore")
        )
    
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:main"),
        InlineKeyboardButton(text="❌ Закрыть", callback_data="admin:close")
    )
    
    return builder.as_markup()


# ===== МЕНЮ МАССОВЫХ ОПЕРАЦИЙ =====

def get_mass_operations_keyboard() -> InlineKeyboardMarkup:
    """Меню массовых операций"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📦 Выдать контейнер всем", callback_data="admin:players:mass:container"),
        InlineKeyboardButton(text="💰 Начислить ресурсы всем", callback_data="admin:players:mass:resources")
    )
    builder.row(
        InlineKeyboardButton(text="🧱 Выдать материал всем", callback_data="admin:players:mass:material"),
        InlineKeyboardButton(text="📊 Выбрать по условию", callback_data="admin:players:mass:filter")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:players")
    )
    
    return builder.as_markup()


# ===== МЕНЮ МЕТРИК =====

def get_metrics_keyboard() -> InlineKeyboardMarkup:
    """Меню метрик"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🔄 Обновить", callback_data="admin:metrics:refresh")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:main"),
        InlineKeyboardButton(text="❌ Закрыть", callback_data="admin:close")
    )
    
    return builder.as_markup()


# ===== НАВИГАЦИЯ =====

def get_navigation_keyboard(page: int, total_pages: int, back_data: str) -> InlineKeyboardMarkup:
    """Универсальная навигация"""
    builder = InlineKeyboardBuilder()
    
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="«", callback_data=f"page:{page-1}"))
    nav_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="page:info"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="»", callback_data=f"page:{page+1}"))
    
    if len(nav_buttons) > 1:
        builder.row(*nav_buttons)
    
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=back_data),
        InlineKeyboardButton(text="❌ Закрыть", callback_data="admin:close")
    )
    
    return builder.as_markup()
