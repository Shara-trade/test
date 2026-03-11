"""
5. АДМИН-ПАНЕЛЬ
Полный функционал управления ботом
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_IDS
from database import db
from admin import AdminManager, PermissionManager, Permission
from admin.broadcast import BroadcastSystem, BroadcastTarget
from admin.balance import BalanceManager
import aiosqlite

router = Router()


class AdminGiveStates(StatesGroup):
    """Состояния для выдачи предметов"""
    waiting_player_id = State()
    waiting_quantity = State()

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
            InlineKeyboardButton(text='🔍 Найти игрока', callback_data='admin_player_search'),
            InlineKeyboardButton(text='💰 Выдать ресурсы', callback_data='admin_player_resources'),
        ],
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


@router.callback_query(F.data == 'admin_player_search')
async def admin_player_search_start(callback: CallbackQuery, state: FSMContext):
    """Поиск игрока"""
    await state.set_state(AdminGiveStates.waiting_player_id)
    await callback.message.edit_text(
        '🔍 <b>ПОИСК ИГРОКА</b>\n\n'
        'Введите ID игрока:',
        parse_mode='HTML'
    )
    await callback.answer()


@router.message(AdminGiveStates.waiting_player_id)
async def admin_player_search_process(message: Message, state: FSMContext):
    """Обработка поиска игрока"""
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    
    try:
        user_id = int(message.text)
    except ValueError:
        await message.answer('❌ Введите число!')
        return
    
    user = await db.get_user(user_id)
    
    if not user:
        await state.clear()
        await message.answer('❌ Игрок не найден!')
        return
    
    await state.clear()
    
    # Показываем профиль игрока с админ-кнопками
    stats = await db.get_user_stats(user_id)
    
    text = (
        f'👤 <b>ПРОФИЛЬ ИГРОКА</b>\n\n'
        f"▸ ID: {user_id}\n"
        f"▸ Ник: @{user.get('username', 'Неизвестно')}\n"
        f"▸ Уровень: {user.get('level', 1)}\n"
        f"▸ Престиж: {user.get('prestige', 0)}\n\n"
        f'💰 <b>РЕСУРСЫ:</b>\n'
        f"▸ Металл: {user.get('metal', 0):,}\n"
        f"▸ Кристаллы: {user.get('crystals', 0):,}\n"
        f"▸ Тёмная материя: {user.get('dark_matter', 0):,}\n"
        f"▸ Кредиты: {user.get('credits', 0):,}\n\n"
        f'⚡ <b>ЭНЕРГИЯ:</b> {user.get("energy", 0):,} / {user.get("max_energy", 1000):,}\n'
        f'🌡 <b>ПЕРЕГРЕВ:</b> {user.get("heat", 0)}%\n\n'
        f'📊 <b>СТАТИСТИКА:</b>\n'
        f"▸ Кликов: {user.get('total_clicks', 0):,}\n"
        f"▸ Добыто: {user.get('total_mined', 0):,}"
    )
    
    keyboard = [
        [
            InlineKeyboardButton(text='💰 +Ресурсы', callback_data=f'admin_add_res_{user_id}'),
            InlineKeyboardButton(text='📦 +Предмет', callback_data=f'admin_add_item_{user_id}'),
        ],
        [
            InlineKeyboardButton(text='⚡ +Энергия', callback_data=f'admin_add_energy_{user_id}'),
            InlineKeyboardButton(text='🔧 Редактировать', callback_data=f'admin_edit_{user_id}'),
        ],
        [
            InlineKeyboardButton(text='🚫 Забанить', callback_data=f'admin_ban_{user_id}'),
            InlineKeyboardButton(text='📜 Логи игрока', callback_data=f'admin_logs_{user_id}'),
        ],
        [
            InlineKeyboardButton(text='◀️ Назад', callback_data='admin_players'),
        ],
    ]
    
    await message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='HTML'
    )


@router.callback_query(F.data.startswith('admin_add_res_'))
async def admin_add_resources_menu(callback: CallbackQuery):
    """Меню добавления ресурсов"""
    if not is_admin(callback.from_user.id):
        await callback.answer('❌ Нет прав', show_alert=True)
        return
    
    user_id = int(callback.data.replace('admin_add_res_', ''))
    
    text = (
        f'💰 <b>ВЫДАТЬ РЕСУРСЫ</b>\n\n'
        f'Игрок ID: {user_id}\n\n'
        f'Выберите ресурс:'
    )
    
    keyboard = [
        [
            InlineKeyboardButton(text='⚙️ +1000 Металл', callback_data=f'admin_res_{user_id}_metal_1000'),
            InlineKeyboardButton(text='⚙️ +10000 Металл', callback_data=f'admin_res_{user_id}_metal_10000'),
        ],
        [
            InlineKeyboardButton(text='💎 +100 Кристаллов', callback_data=f'admin_res_{user_id}_crystals_100'),
            InlineKeyboardButton(text='💎 +1000 Кристаллов', callback_data=f'admin_res_{user_id}_crystals_1000'),
        ],
        [
            InlineKeyboardButton(text='⚫ +10 Тёмной материи', callback_data=f'admin_res_{user_id}_dark_matter_10'),
            InlineKeyboardButton(text='⚫ +100 Тёмной материи', callback_data=f'admin_res_{user_id}_dark_matter_100'),
        ],
        [
            InlineKeyboardButton(text='💵 +1000 Кредитов', callback_data=f'admin_res_{user_id}_credits_1000'),
            InlineKeyboardButton(text='💵 +10000 Кредитов', callback_data=f'admin_res_{user_id}_credits_10000'),
        ],
        [
            InlineKeyboardButton(text='◀️ Назад', callback_data='admin_players'),
        ],
    ]
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data.startswith('admin_res_'))
async def admin_add_resources_execute(callback: CallbackQuery):
    """Выдача ресурсов"""
    if not is_admin(callback.from_user.id):
        await callback.answer('❌ Нет прав', show_alert=True)
        return
    
    parts = callback.data.split('_')
    user_id = int(parts[2])
    resource = parts[3]
    amount = int(parts[4])
    
    # Выдаём ресурс
    await db.update_user_resources(user_id, **{resource: amount})
    
    # Логируем
    await log_admin_action(
        admin_id=callback.from_user.id,
        action='give_resource',
        target_user_id=user_id,
        details=f'{resource} +{amount}'
    )
    
    await callback.answer(f'✅ Выдано {amount} {resource}', show_alert=True)
    
    # Обновляем меню
    await admin_add_resources_menu(callback)


@router.callback_query(F.data.startswith('admin_add_energy_'))
async def admin_add_energy(callback: CallbackQuery):
    """Восстановить энергию игроку"""
    if not is_admin(callback.from_user.id):
        await callback.answer('❌ Нет прав', show_alert=True)
        return
    
    user_id = int(callback.data.replace('admin_add_energy_', ''))
    
    user = await db.get_user(user_id)
    max_energy = user.get('max_energy', 1000)
    
    # Восстанавливаем энергию до максимума
    await db.update_user_resources(user_id, energy=max_energy)
    
    # Логируем
    await log_admin_action(
        admin_id=callback.from_user.id,
        action='restore_energy',
        target_user_id=user_id,
        details=f'Energy restored to {max_energy}'
    )
    
    await callback.answer(f'✅ Энергия восстановлена ({max_energy})', show_alert=True)


@router.callback_query(F.data.startswith('admin_add_item_'))
async def admin_add_item_to_player(callback: CallbackQuery):
    """Перейти к выдаче предмета конкретному игроку"""
    if not is_admin(callback.from_user.id):
        await callback.answer('❌ Нет прав', show_alert=True)
        return
    
    user_id = int(callback.data.replace('admin_add_item_', ''))
    
    # Сохраняем ID игрока и переходим к выбору предмета
    from core.cache import cache
    await cache.set(f'admin_target:{callback.from_user.id}', user_id, ttl=300)
    
    await admin_give_item_start(callback)


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
            InlineKeyboardButton(text='🎁 Выдать предмет', callback_data='admin_give_item'),
            InlineKeyboardButton(text='➕ Создать предмет', callback_data='admin_items_create'),
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


# ==================== ВЫДАЧА ПРЕДМЕТОВ ====================

@router.callback_query(F.data == 'admin_give_item')
async def admin_give_item_start(callback: CallbackQuery):
    """Начало выдачи предмета - выбор типа"""
    if not is_admin(callback.from_user.id):
        await callback.answer('❌ Нет прав', show_alert=True)
        return
    
    text = (
        '🎁 <b>ВЫДАТЬ ПРЕДМЕТ</b>\n\n'
        'Выберите категорию:'
    )
    
    keyboard = [
        [
            InlineKeyboardButton(text='⚙️ Модули', callback_data='admin_give_category_module'),
            InlineKeyboardButton(text='🤖 Дроны', callback_data='admin_give_category_drone'),
        ],
        [
            InlineKeyboardButton(text='📦 Контейнеры', callback_data='admin_give_category_container'),
            InlineKeyboardButton(text='💎 Ресурсы', callback_data='admin_give_category_resource'),
        ],
        [
            InlineKeyboardButton(text='🔧 Материалы', callback_data='admin_give_category_material'),
            InlineKeyboardButton(text='📋 Все предметы', callback_data='admin_give_category_all'),
        ],
        [
            InlineKeyboardButton(text='◀️ Назад', callback_data='admin_items'),
        ],
    ]
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data.startswith('admin_give_category_'))
async def admin_give_item_select(callback: CallbackQuery):
    """Выбор предмета из категории"""
    if not is_admin(callback.from_user.id):
        await callback.answer('❌ Нет прав', show_alert=True)
        return
    
    category = callback.data.replace('admin_give_category_', '')
    
    # Получаем предметы категории
    items = await get_items_by_category(category)
    
    if not items:
        await callback.answer('В этой категории нет предметов', show_alert=True)
        return
    
    text = f'🎁 <b>ВЫБЕРИТЕ ПРЕДМЕТ</b>\n\nКатегория: {category}\n\nВыберите предмет:'
    
    keyboard = []
    row = []
    
    for item in items[:12]:  # Максимум 12 предметов
        icon = item.get('icon', '📦')
        name = item.get('name', item['item_key'])[:12]
        rarity = item.get('rarity', 'common')
        
        rarity_colors = {
            'relic': '⚜️',
            'legendary': '💛',
            'epic': '💜',
            'rare': '🔸',
            'common': '🔹'
        }
        rarity_icon = rarity_colors.get(rarity, '')
        
        row.append(InlineKeyboardButton(
            text=f'{icon} {name} {rarity_icon}',
            callback_data=f'admin_give_select:{item["item_key"]}'
        ))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    keyboard.append([
        InlineKeyboardButton(text='◀️ Назад', callback_data='admin_give_item')
    ])
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data.startswith('admin_give_select:'))
async def admin_give_item_player(callback: CallbackQuery):
    """Выбор игрока для выдачи"""
    if not is_admin(callback.from_user.id):
        await callback.answer('❌ Нет прав', show_alert=True)
        return
    
    item_key = callback.data.split(':', 1)[-1]
    
    # Получаем информацию о предмете
    item = await db.get_item_info(item_key)
    
    if not item:
        await callback.answer('Предмет не найден', show_alert=True)
        return
    
    # Сохраняем в cache (временно)
    from core.cache import cache
    await cache.set(f'admin_give:{callback.from_user.id}', {'item_key': item_key}, ttl=300)
    
    icon = item.get('icon', '📦')
    name = item.get('name', item_key)
    rarity = item.get('rarity', 'common')
    
    # Проверяем, есть ли предвыбранный игрок
    target_user_id = await cache.get(f'admin_target:{callback.from_user.id}')
    
    if target_user_id:
        # Сразу переходим к подтверждению
        give_data = {'item_key': item_key, 'target_user_id': target_user_id}
        await cache.set(f'admin_give:{callback.from_user.id}', give_data, ttl=300)
        await cache.delete(f'admin_target:{callback.from_user.id}')
        
        # Создаём фейковый callback для перехода к подтверждению
        class FakeCallback:
            def __init__(self, data, message, from_user):
                self.data = data
                self.message = message
                self.from_user = from_user
            
            async def answer(self, text=None, show_alert=False):
                pass
        
        fake_callback = FakeCallback(
            f'admin_give_player_{target_user_id}',
            callback.message,
            callback.from_user
        )
        await admin_give_item_confirm(fake_callback)
        return
    
    text = (
        f'🎁 <b>ВЫДАТЬ ПРЕДМЕТ</b>\n\n'
        f'Предмет: {icon} <b>{name}</b>\n'
        f'Редкость: {rarity}\n'
        f'Key: <code>{item_key}</code>\n\n'
        f'Введите ID игрока или выберите из списка:'
    )
    
    # Получаем последних активных игроков
    recent_players = await get_recent_active_players(5)
    
    keyboard = []
    
    for player in recent_players:
        username = player.get('username', 'Unknown')
        user_id = player['user_id']
        keyboard.append([
            InlineKeyboardButton(
                text=f'👤 {username} ({user_id})',
                callback_data=f'admin_give_player_{user_id}'
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(text='🔍 Ввести ID', callback_data='admin_give_input_id')
    ])
    keyboard.append([
        InlineKeyboardButton(text='◀️ Назад', callback_data='admin_give_item')
    ])
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data == 'admin_give_input_id')
async def admin_give_input_id(callback: CallbackQuery, state: FSMContext):
    """Запрос ввода ID игрока"""
    await state.set_state(AdminGiveStates.waiting_player_id)
    await callback.message.edit_text(
        '🔍 <b>ВВОД ID ИГРОКА</b>\n\n'
        'Введите ID игрока (число):',
        parse_mode='HTML'
    )
    await callback.answer()


@router.message(AdminGiveStates.waiting_player_id)
async def admin_give_process_id(message: Message, state: FSMContext):
    """Обработка введённого ID"""
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    
    try:
        target_user_id = int(message.text)
    except ValueError:
        await message.answer('❌ Введите число!')
        return
    
    # Проверяем существование игрока
    target_user = await db.get_user(target_user_id)
    
    if not target_user:
        await message.answer('❌ Игрок не найден!')
        return
    
    # Получаем сохранённый предмет
    from core.cache import cache
    give_data = await cache.get(f'admin_give:{message.from_user.id}')
    
    if not give_data:
        await state.clear()
        await message.answer('❌ Сессия истекла. Начните заново.')
        return
    
    item_key = give_data['item_key']
    item = await db.get_item_info(item_key)
    
    # Сохраняем ID игрока
    give_data['target_user_id'] = target_user_id
    await cache.set(f'admin_give:{message.from_user.id}', give_data, ttl=300)
    await state.clear()
    
    icon = item.get('icon', '📦')
    name = item.get('name', item_key)
    target_username = target_user.get('username', str(target_user_id))
    
    text = (
        f'✅ <b>ПОДТВЕРЖДЕНИЕ ВЫДАЧИ</b>\n\n'
        f'Предмет: {icon} <b>{name}</b>\n'
        f'Кому: @{target_username} (ID: {target_user_id})\n'
        f'Количество: 1\n\n'
        f'Подтвердить выдачу?'
    )
    
    keyboard = [
        [
            InlineKeyboardButton(text='✅ Выдать x1', callback_data=f'admin_give_confirm_1'),
            InlineKeyboardButton(text='✅ x5', callback_data=f'admin_give_confirm_5'),
            InlineKeyboardButton(text='✅ x10', callback_data=f'admin_give_confirm_10'),
        ],
        [
            InlineKeyboardButton(text='❌ Отмена', callback_data='admin_give_item')
        ]
    ]
    
    await message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='HTML'
    )


@router.callback_query(F.data.startswith('admin_give_player_'))
async def admin_give_item_confirm(callback: CallbackQuery):
    """Подтверждение выдачи"""
    if not is_admin(callback.from_user.id):
        await callback.answer('❌ Нет прав', show_alert=True)
        return
    
    target_user_id = int(callback.data.replace('admin_give_player_', ''))
    
    # Получаем сохранённый предмет
    from core.cache import cache
    give_data = await cache.get(f'admin_give:{callback.from_user.id}')
    
    if not give_data:
        await callback.answer('Сессия истекла. Начните заново.', show_alert=True)
        return
    
    item_key = give_data['item_key']
    
    # Получаем информацию
    item = await db.get_item_info(item_key)
    target_user = await db.get_user(target_user_id)
    
    if not target_user:
        await callback.answer('Игрок не найден', show_alert=True)
        return
    
    icon = item.get('icon', '📦')
    name = item.get('name', item_key)
    target_username = target_user.get('username', str(target_user_id))
    
    # Сохраняем ID игрока
    give_data['target_user_id'] = target_user_id
    await cache.set(f'admin_give:{callback.from_user.id}', give_data, ttl=300)
    
    text = (
        f'✅ <b>ПОДТВЕРЖДЕНИЕ ВЫДАЧИ</b>\n\n'
        f'Предмет: {icon} <b>{name}</b>\n'
        f'Кому: @{target_username} (ID: {target_user_id})\n'
        f'Количество: 1\n\n'
        f'Подтвердить выдачу?'
    )
    
    keyboard = [
        [
            InlineKeyboardButton(text='✅ Выдать x1', callback_data=f'admin_give_confirm_1'),
            InlineKeyboardButton(text='✅ x5', callback_data=f'admin_give_confirm_5'),
            InlineKeyboardButton(text='✅ x10', callback_data=f'admin_give_confirm_10'),
        ],
        [
            InlineKeyboardButton(text='❌ Отмена', callback_data='admin_give_item')
        ]
    ]
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data.startswith('admin_give_confirm_'))
async def admin_give_item_execute(callback: CallbackQuery):
    """Выполнение выдачи"""
    if not is_admin(callback.from_user.id):
        await callback.answer('❌ Нет прав', show_alert=True)
        return
    
    quantity = int(callback.data.replace('admin_give_confirm_', ''))
    
    # Получаем данные
    from core.cache import cache
    give_data = await cache.get(f'admin_give:{callback.from_user.id}')
    
    if not give_data:
        await callback.answer('Сессия истекла', show_alert=True)
        return
    
    item_key = give_data['item_key']
    target_user_id = give_data['target_user_id']
    
    # Выдаём предмет
    result = await db.add_item(target_user_id, item_key, quantity)
    
    if result.get('success'):
        # Логируем
        await log_admin_action(
            admin_id=callback.from_user.id,
            action='give_item',
            target_user_id=target_user_id,
            details=f'{item_key} x{quantity}'
        )
        
        # Получаем имена
        item = await db.get_item_info(item_key)
        target_user = await db.get_user(target_user_id)
        
        icon = item.get('icon', '📦') if item else '📦'
        name = item.get('name', item_key) if item else item_key
        target_username = target_user.get('username', str(target_user_id)) if target_user else str(target_user_id)
        
        await callback.answer(f'✅ Выдано {icon} {name} x{quantity} игроку @{target_username}', show_alert=True)
        
        # Очищаем cache
        await cache.delete(f'admin_give:{callback.from_user.id}')
        
        # Возвращаемся в меню
        await admin_items_menu(callback)
    else:
        error_msg = result.get('error', 'Unknown error')
        
        # Логируем ошибку
        await log_admin_action(
            admin_id=callback.from_user.id,
            action='give_item_failed',
            target_user_id=target_user_id,
            details=f'{item_key} x{quantity} - ERROR: {error_msg}'
        )
        
        await callback.answer(f'❌ Ошибка: {error_msg}', show_alert=True)


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

async def get_items_by_category(category: str) -> list:
    """Получить предметы по категории"""
    async with aiosqlite.connect(db.db_path) as conn:
        conn.row_factory = aiosqlite.Row
        
        if category == 'all':
            query = "SELECT * FROM items ORDER BY item_type, rarity"
        else:
            category_map = {
                'module': 'module',
                'drone': 'drone',
                'container': 'container',
                'resource': 'resource',
                'material': 'material'
            }
            item_type = category_map.get(category, category)
            query = "SELECT * FROM items WHERE item_type = ? ORDER BY rarity"
        
        if category == 'all':
            async with conn.execute(query) as cursor:
                rows = await cursor.fetchall()
        else:
            async with conn.execute(query, (item_type,)) as cursor:
                rows = await cursor.fetchall()
        
        return [dict(r) for r in rows]


async def get_recent_active_players(limit: int = 5) -> list:
    """Получить последних активных игроков"""
    async with aiosqlite.connect(db.db_path) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute(
            "SELECT user_id, username FROM users WHERE is_banned = 0 ORDER BY last_activity DESC LIMIT ?",
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def log_admin_action(admin_id: int, action: str, target_user_id: int = None, details: str = None):
    """Залогировать действие админа"""
    async with aiosqlite.connect(db.db_path) as conn:
        await conn.execute(
            "INSERT INTO admin_logs (admin_id, action, target_user_id, details) VALUES (?, ?, ?, ?)",
            (admin_id, action, target_user_id, details)
        )
        await conn.commit()


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
