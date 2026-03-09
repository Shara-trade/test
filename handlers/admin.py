"""
5. АДМИН-ПАНЕЛЬ
Полный функционал управления ботом
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_IDS
from database import db
from admin import AdminManager, PermissionManager, Permission
from admin.broadcast import BroadcastSystem, BroadcastTarget
from admin.balance import BalanceManager

router = Router()

# Инициализация менеджеров
balance_manager = BalanceManager()


def is_admin(user_id: int) -> bool:
    """Проверка прав админа"""
    return user_id in ADMIN_IDS


def check_permission(user_id: int, permission: Permission) -> bool:
    """Проверка конкретного права"""
    if user_id in ADMIN_IDS:
        return True
    return PermissionManager.check_permission(user_id, permission, {})


@router.message(Command('admin'))
async def cmd_admin(message: Message):
    """Главное меню админ-панели"""
    if not is_admin(message.from_user.id):
        await message.answer('❌ У вас нет доступа к админ-панели.')
        return

    # Получаем статистику
    stats = await AdminManager.get_stats(db)
    
    text = (
        '🛠 <b>АДМИН-ПАНЕЛЬ</b>\n\n'
        '<b>📊 СТАТИСТИКА:</b>\n'
        f'▸ Всего игроков: {stats.total_players:,}\n'
        f'▸ Активных сегодня: {stats.active_today:,}\n'
        f'▸ Активных онлайн: {stats.active_online:,}\n'
        f'▸ Всего дронов: {stats.total_drones:,}\n'
        f'▸ Забанено: {stats.banned_players:,}\n\n'
        'Выберите раздел:'
    )

    keyboard = [
        [
            InlineKeyboardButton(text='👥 Игроки', callback_data='admin_players'),
            InlineKeyboardButton(text='📦 Предметы', callback_data='admin_items'),
        ],
        [
            InlineKeyboardButton(text='🤖 Дроны', callback_data='admin_drones'),
            InlineKeyboardButton(text='🏪 Рынок', callback_data='admin_market'),
        ],
        [
            InlineKeyboardButton(text='👥 Кланы', callback_data='admin_clans'),
            InlineKeyboardButton(text='🎯 Ивенты', callback_data='admin_events'),
        ],
        [
            InlineKeyboardButton(text='📢 Рассылка', callback_data='admin_broadcast'),
            InlineKeyboardButton(text='📊 Логи', callback_data='admin_logs'),
        ],
        [
            InlineKeyboardButton(text='⚖️ Балансировка', callback_data='admin_balance'),
            InlineKeyboardButton(text='⚙️ Настройки', callback_data='admin_settings'),
        ],
    ]

    await message.answer(
        text, 
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='HTML'
    )


# ==================== УПРАВЛЕНИЕ ИГРОКАМИ ====================

@router.callback_query(F.data == 'admin_players')
async def admin_players_menu(callback: CallbackQuery):
    """Меню управления игроками"""
    if not is_admin(callback.from_user.id):
        await callback.answer('❌ Нет прав', show_alert=True)
        return
    
    text = (
        '👥 <b>УПРАВЛЕНИЕ ИГРОКАМИ</b>\n\n'
        'Поиск игрока по ID или @username:'
    )
    
    keyboard = [
        [
            InlineKeyboardButton(text='📋 Последние', callback_data='admin_players_recent'),
            InlineKeyboardButton(text='🚫 Забаненные', callback_data='admin_players_banned'),
        ],
        [
            InlineKeyboardButton(text='💎 Премиум', callback_data='admin_players_premium'),
            InlineKeyboardButton(text='📊 Топ по уровню', callback_data='admin_players_top'),
        ],
        [
            InlineKeyboardButton(text='◀️ Назад', callback_data='admin_back'),
        ],
    ]
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data == 'admin_players_search')
async def admin_players_search(callback: CallbackQuery, state: dict):
    """Поиск игрока"""
    await callback.message.edit_text(
        '🔍<b>ПОИСК ИГРОКА</b>\n\n'
        'Введите ID или @username игрока:',
        parse_mode='HTML'
    )
    # Здесь должна быть машина состояний для ввода


# ==================== УПРАВЛЕНИЕ ПРЕДМЕТАМИ ====================

@router.callback_query(F.data == 'admin_items')
async def admin_items_menu(callback: CallbackQuery):
    """Меню управления предметами"""
    if not is_admin(callback.from_user.id):
        await callback.answer('❌ Нет прав', show_alert=True)
        return
    
    text = '📦 <b>УПРАВЛЕНИЕ ПРЕДМЕТАМИ</b>'
    
    keyboard = [
        [
            InlineKeyboardButton(text='➕ Создать предмет', callback_data='admin_items_create'),
            InlineKeyboardButton(text='✏️ Редактировать', callback_data='admin_items_edit'),
        ],
        [
            InlineKeyboardButton(text='📋 Список всех', callback_data='admin_items_list'),
            InlineKeyboardButton(text='📊 Статистика', callback_data='admin_items_stats'),
        ],
        [
            InlineKeyboardButton(text='◀️ Назад', callback_data='admin_back'),
        ],
    ]
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='HTML'
    )
    await callback.answer()


# ==================== УПРАВЛЕНИЕ РЫНКОМ ====================

@router.callback_query(F.data == 'admin_market')
async def admin_market_menu(callback: CallbackQuery):
    """Меню управления рынком"""
    if not is_admin(callback.from_user.id):
        await callback.answer('❌ Нет прав', show_alert=True)
        return
    
    stats = await AdminManager.get_market_stats(db)
    
    text = (
        '🏪 <b>УПРАВЛЕНИЕ РЫНКОМ</b>\n\n'
        f'▸ Активных лотов: {stats["active_lots"]}\n'
        f'▸ Просроченных: {stats["expired_lots"]}\n'
        f'▸ Жалоб: {stats["complaints"]}\n'
        f'▸ Комиссия: {int(stats["commission_rate"] * 100)}%'
    )
    
    keyboard = [
        [
            InlineKeyboardButton(text='📋 Просмотр лотов', callback_data='admin_market_lots'),
            InlineKeyboardButton(text='🗑 Удалить лот', callback_data='admin_market_delete'),
        ],
        [
            InlineKeyboardButton(text='⚠️ Споры', callback_data='admin_market_disputes'),
            InlineKeyboardButton(text='⚖️ Комиссия', callback_data='admin_market_commission'),
        ],
        [
            InlineKeyboardButton(text='📊 Статистика', callback_data='admin_market_stats'),
            InlineKeyboardButton(text='◀️ Назад', callback_data='admin_back'),
        ],
    ]
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='HTML'
    )
    await callback.answer()


# ==================== РАССЫЛКА ====================

@router.callback_query(F.data == 'admin_broadcast')
async def admin_broadcast_menu(callback: CallbackQuery):
    """Меню рассылки"""
    if not is_admin(callback.from_user.id):
        await callback.answer('❌ Нет прав', show_alert=True)
        return
    
    text = (
        '📢 <b>РАССЫЛКА СООБЩЕНИЙ</b>\n\n'
        'Выберите целевую аудиторию:'
    )
    
    keyboard = [
        [
            InlineKeyboardButton(text='✅ Все игроки', callback_data='broadcast_all'),
            InlineKeyboardButton(text='✅ Активные 7д', callback_data='broadcast_active_7d'),
        ],
        [
            InlineKeyboardButton(text='✅ Премиум', callback_data='broadcast_premium'),
            InlineKeyboardButton(text='✅ По уровню', callback_data='broadcast_by_level'),
        ],
        [
            InlineKeyboardButton(text='📋 История рассылок', callback_data='broadcast_history'),
            InlineKeyboardButton(text='◀️ Назад', callback_data='admin_back'),
        ],
    ]
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='HTML'
    )
    await callback.answer()


# ==================== БАЛАНСИРОВКА ====================

@router.callback_query(F.data == 'admin_balance')
async def admin_balance_menu(callback: CallbackQuery):
    """Меню балансировки"""
    if not is_admin(callback.from_user.id):
        await callback.answer('❌ Нет прав', show_alert=True)
        return
    
    text = (
        '⚖️ <b>БАЛАНСИРОВКА</b>\n\n'
        'Выберите категорию параметров:'
    )
    
    keyboard = [
        [
            InlineKeyboardButton(text='⛏ Добыча', callback_data='balance_mining'),
            InlineKeyboardButton(text='⚡ Энергия', callback_data='balance_energy'),
        ],
        [
            InlineKeyboardButton(text='🌡 Перегрев', callback_data='balance_heat'),
            InlineKeyboardButton(text='💥 Криты', callback_data='balance_crit'),
        ],
        [
            InlineKeyboardButton(text='🤖 Дроны', callback_data='balance_drones'),
            InlineKeyboardButton(text='💰 Экономика', callback_data='balance_economy'),
        ],
        [
            InlineKeyboardButton(text='📦 Контейнеры', callback_data='balance_containers'),
            InlineKeyboardButton(text='📤 Экспорт', callback_data='balance_export'),
        ],
        [
            InlineKeyboardButton(text='◀️ Назад', callback_data='admin_back'),
        ],
    ]
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data.startswith('balance_'))
async def admin_balance_category(callback: CallbackQuery):
    """Просмотр категории балансировки"""
    category = callback.data.replace('balance_', '')
    
    if category == 'export':
        # Экспорт параметров в JSON
        json_data = balance_manager.export_to_json()
        await callback.message.answer(
            f'📤 Экспорт параметров:\n\n<code>{json_data}</code>',
            parse_mode='HTML'
        )
        await callback.answer('Параметры экспортированы')
        return
    
    text = balance_manager.format_category_params(category)
    
    keyboard = [
        [
            InlineKeyboardButton(text='✏️ Изменить', callback_data=f'balance_edit_{category}'),
            InlineKeyboardButton(text='🔄 Сбросить', callback_data=f'balance_reset_{category}'),
        ],
        [
            InlineKeyboardButton(text='◀️ Назад', callback_data='admin_balance'),
        ],
    ]
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='HTML'
    )
    await callback.answer()


# ==================== ЛОГИ ====================

@router.callback_query(F.data == 'admin_logs')
async def admin_logs_menu(callback: CallbackQuery):
    """Меню логов"""
    if not is_admin(callback.from_user.id):
        await callback.answer('❌ Нет прав', show_alert=True)
        return
    
    text = (
        '📊 <b>ЛОГИ И СТАТИСТИКА</b>\n\n'
        'Выберите тип логов:'
    )
    
    keyboard = [
        [
            InlineKeyboardButton(text='📜 Действия админов', callback_data='logs_admin'),
            InlineKeyboardButton(text='🚫 Баны', callback_data='logs_bans'),
        ],
        [
            InlineKeyboardButton(text='📦 Выдачи', callback_data='logs_gives'),
            InlineKeyboardButton(text='📢 Рассылки', callback_data='logs_broadcasts'),
        ],
        [
            InlineKeyboardButton(text='📈 Общая статистика', callback_data='logs_stats'),
            InlineKeyboardButton(text='💰 Экономика', callback_data='logs_economy'),
        ],
        [
            InlineKeyboardButton(text='◀️ Назад', callback_data='admin_back'),
        ],
    ]
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='HTML'
    )
    await callback.answer()


# ==================== НАВИГАЦИЯ ====================

@router.callback_query(F.data == 'admin_back')
async def admin_back(callback: CallbackQuery):
    """Возврат в главное меню"""
    await cmd_admin(callback.message)


@router.callback_query(F.data == 'admin_drones')
async def admin_drones_menu(callback: CallbackQuery):
    """Меню дронов"""
    await callback.answer('🤖 Управление дронами - в разработке')


@router.callback_query(F.data == 'admin_clans')
async def admin_clans_menu(callback: CallbackQuery):
    """Меню кланов"""
    await callback.answer('👥 Управление кланами - в разработке')


@router.callback_query(F.data == 'admin_events')
async def admin_events_menu(callback: CallbackQuery):
    """Меню ивентов"""
    await callback.answer('🎯 Управление ивентами - в разработке')


@router.callback_query(F.data == 'admin_settings')
async def admin_settings_menu(callback: CallbackQuery):
    """Меню настроек"""
    await callback.answer('⚙️ Настройки бота - в разработке')
