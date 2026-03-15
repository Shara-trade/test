"""
Хендлеры системы дронов.
Техническое задание: dron.txt
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import logging

from database import db
from game.drones import (
    DroneSystem, DRONE_CONFIG, DRONE_TYPES, LEVEL_EMOJI,
    MAX_HIRED_DRONES, MAX_DRONE_LEVEL
)

router = Router()
logger = logging.getLogger(__name__)


# ==================== ГЛАВНОЕ МЕНЮ АНГАРА ====================

@router.message(Command('angar'))
@router.message(F.text == '🚀 Ангар')
async def cmd_angar(message: Message):
    """Команда /angar или кнопка Ангар"""
    await show_angar(message, message.from_user.id)


async def show_angar(message_or_callback, user_id: int, edit: bool = False):
    """Показать главное меню Ангара"""
    from aiogram.types import Message
    
    # Получаем данные пользователя
    user = await db.get_user(user_id)
    if not user:
        if isinstance(message_or_callback, Message):
            await message_or_callback.answer('❌ Пользователь не найден')
        return

    # Обновляем хранилище если есть активные дроны
    if user.get('drones_hired', 0) > 0:
        await db.update_drone_storage(user_id)
        user = await db.get_user(user_id)  # Перечитываем
    
    # Получаем данные о дронах
    drones_data = await db.get_user_drones(user_id)
    
    # Считаем общее количество дронов
    total_drones = DroneSystem.calculate_total_drones(drones_data)
    drones_hired = user.get('drones_hired', 0)
    
    # Доход в минуту (только от нанятых)
    income = DroneSystem.calculate_income_per_minute(drones_data, drones_hired)
    
    # Формируем текст
    text = (
        f"🚀 <b>Твой ангар:</b>\n"
        f"🚁 Дронов в ангаре: {total_drones}\n"
        f"🚁 Дронов в найме: {drones_hired}/{MAX_HIRED_DRONES}\n\n"
        f"Доход в минуту:\n"
        f"▸ ⚙️ Металл: {income['metal']:,}\n"
        f"▸ 💎 Кристаллы: {income['crystals']:,}\n"
        f"▸ 🕳️ Тёмная материя: {income['dark_matter']:,}"
    )

    # Хранилище
    storage_metal = user.get('storage_metal', 0) or 0
    storage_crystal = user.get('storage_crystal', 0) or 0
    storage_dark = user.get('storage_dark', 0) or 0
    
    if storage_metal > 0 or storage_crystal > 0 or storage_dark > 0:
        text += (
            f"\n\nХранилище дронов:\n"
            f"▸ ⚙️ Металл: {storage_metal:,}\n"
            f"▸ 💎 Кристаллы: {storage_crystal:,}\n"
            f"▸ 🕳️ Тёмная материя: {storage_dark:,}"
        )
    
    # Клавиатура
    keyboard = []

    # Кнопка "Собрать" если есть ресурсы в хранилище
    if storage_metal > 0 or storage_crystal > 0 or storage_dark > 0:
        keyboard.append([
            InlineKeyboardButton(text="📥 Собрать", callback_data="drone_collect")
        ])
    # Кнопка "Отправить" если есть свободные дроны и нет активной миссии
    elif total_drones > 0 and drones_hired == 0:
        keyboard.append([
            InlineKeyboardButton(text="🚀 Отправить", callback_data="drone_send")
        ])

    keyboard.extend([
        [
            InlineKeyboardButton(text="🤖 Дроны", callback_data="drone_types"),
            InlineKeyboardButton(text="🛒 Магазин дронов", callback_data="drone_shop")
        ],
        [
            InlineKeyboardButton(text="❌ Закрыть", callback_data="drone_close")
        ]
    ])

    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    if edit and hasattr(message_or_callback, 'edit_text'):
        try:
            await message_or_callback.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
        except Exception as e:
            logger.debug(f"Edit failed: {e}")
    else:
        await message_or_callback.answer(text, reply_markup=reply_markup, parse_mode='HTML')


@router.callback_query(F.data == 'drone_angar')
async def on_drone_angar(callback: CallbackQuery):
    """Возврат в ангар"""
    await show_angar(callback.message, callback.from_user.id, edit=True)
    await callback.answer()


@router.callback_query(F.data == 'drone_close')
async def on_drone_close(callback: CallbackQuery):
    """Закрыть меню дронов"""
    try:
        await callback.message.delete()
    except:
        pass
    await callback.answer()


# ==================== МЕНЮ ТИПОВ ДРОНОВ ====================

@router.callback_query(F.data == 'drone_types')
async def on_drone_types(callback: CallbackQuery):
    """Меню типов дронов"""
    user_id = callback.from_user.id
    
    # Получаем данные
    drones_data = await db.get_user_drones(user_id)
    user = await db.get_user(user_id)
    has_premium = user.get('has_premium', 0) if user else 0
    
    text = "🤖 <b>Дроны:</b>"
    
    keyboard = []
    
    for drone_type in DRONE_TYPES:
        config = DRONE_CONFIG[drone_type]
        
        # Считаем количество дронов этого типа
        count = 0
        for lvl in range(1, 6):
            count += drones_data.get(f"{drone_type}_lvl{lvl}", 0)
        
        keyboard.append([
            InlineKeyboardButton(
                text=f"{config['emoji']} {config['name']} ({count})",
                callback_data=f"drone_card_{drone_type}_1"
            )
        ])
    
    # Кнопка "Улучшить всё" для премиум
    if has_premium:
        keyboard.append([
            InlineKeyboardButton(text="💎 Улучшить всё", callback_data="drone_upgrade_all")
        ])
    
    keyboard.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="drone_angar")
    ])
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='HTML'
    )
    await callback.answer()


# ==================== КАРТОЧКА ДРОНА ====================

@router.callback_query(F.data.startswith('drone_card_'))
async def on_drone_card(callback: CallbackQuery):
    """Карточка дрона определённого уровня"""
    # Парсим данные
    parts = callback.data.split('_')
    drone_type = parts[2]
    level = int(parts[3])
    
    user_id = callback.from_user.id
    drones_data = await db.get_user_drones(user_id)
    
    config = DRONE_CONFIG.get(drone_type)
    if not config:
        await callback.answer("❌ Неизвестный тип дрона")
        return
    
    # Данные дрона
    count = drones_data.get(f"{drone_type}_lvl{level}", 0)
    income = DroneSystem.get_income(drone_type, level)
    slots = DroneSystem.get_module_slots(level)
    emoji = DroneSystem.get_level_emoji(level)
    
    # Формируем текст дохода
    income_parts = []
    if income['metal'] > 0:
        income_parts.append(f"+{income['metal']} ⚙️")
    if income['crystals'] > 0:
        income_parts.append(f"+{income['crystals']} 💎")
    if income['dark_matter'] > 0:
        income_parts.append(f"+{income['dark_matter']} 🕳️")
    income_text = " ".join(income_parts)
    
    text = (
        f"{emoji} <b>{config['name']}:</b>\n"
        f"▸ Уровень: {level}\n"
        f"▸ Доход: {income_text}\n"
        f"▸ Слотов модулей: {slots} 🧩\n"
        f"▸ Количество: {count}"
    )
    
    # Клавиатура
    keyboard = []
    
    # Навигация по уровням
    nav_buttons = []
    
    if level > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="«", callback_data=f"drone_card_{drone_type}_{level-1}")
        )
    
    # Кнопки действий
    nav_buttons.append(
        InlineKeyboardButton(text="🤚", callback_data=f"drone_hire_{drone_type}_{level}")
    )
    nav_buttons.append(
        InlineKeyboardButton(text="💰", callback_data=f"drone_sell_{drone_type}_{level}")
    )
    
    if level < MAX_DRONE_LEVEL:
        nav_buttons.append(
            InlineKeyboardButton(text="⭐️", callback_data=f"drone_upgrade_menu_{drone_type}_{level}")
        )
    
    if level < MAX_DRONE_LEVEL:
        # Проверяем есть ли дроны следующего уровня
        next_count = drones_data.get(f"{drone_type}_lvl{level+1}", 0)
        if next_count > 0:
            nav_buttons.append(
                InlineKeyboardButton(text="»", callback_data=f"drone_card_{drone_type}_{level+1}")
            )
    
    keyboard.append(nav_buttons)
    
    keyboard.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="drone_types"),
        InlineKeyboardButton(text="❌ Закрыть", callback_data="drone_close")
    ])
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='HTML'
    )
    await callback.answer()


# ==================== МАГАЗИН ДРОНОВ ====================

@router.callback_query(F.data == 'drone_shop')
async def on_drone_shop(callback: CallbackQuery):
    """Магазин дронов - начинаем с базового"""
    await show_shop_drone(callback.message, callback.from_user.id, 'basic', edit=True)
    await callback.answer()


@router.callback_query(F.data.startswith('drone_shop_'))
async def on_drone_shop_nav(callback: CallbackQuery):
    """Навигация по магазину"""
    drone_type = callback.data.split('_')[2]
    await show_shop_drone(callback.message, callback.from_user.id, drone_type, edit=True)
    await callback.answer()


async def show_shop_drone(message, user_id: int, drone_type: str, edit: bool = False):
    """Показать карточку дрона в магазине"""
    config = DRONE_CONFIG.get(drone_type)
    if not config:
        return
    
    user = await db.get_user(user_id)
    if not user:
        return
    
    price = config['price']
    income = DroneSystem.get_income(drone_type, 1)
    
    # Формируем текст цены
    price_parts = []
    if price['metal'] > 0:
        price_parts.append(f"{price['metal']:,} ⚙️")
    if price['crystals'] > 0:
        price_parts.append(f"{price['crystals']:,} 💎")
    if price['dark_matter'] > 0:
        price_parts.append(f"{price['dark_matter']:,} 🕳️")
    price_text = " + ".join(price_parts)
    
    # Формируем текст дохода
    income_parts = []
    if income['metal'] > 0:
        income_parts.append(f"+{income['metal']} ⚙️")
    if income['crystals'] > 0:
        income_parts.append(f"+{income['crystals']} 💎")
    if income['dark_matter'] > 0:
        income_parts.append(f"+{income['dark_matter']} 🕳️")
    income_text = " ".join(income_parts)
    
    text = (
        f"🛒 <b>Магазин дронов:</b>\n"
        f"{config['emoji']} {config['name']}\n"
        f"▸ Цена: {price_text}\n"
        f"▸ Доход: {income_text}\n"
        f"▸ ⚪️ Уровень: 1"
    )
    
    # Находим индекс текущего типа
    current_idx = DRONE_TYPES.index(drone_type)
    
    keyboard = []
    
    # Навигация
    nav_buttons = []
    if current_idx > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="«", callback_data=f"drone_shop_{DRONE_TYPES[current_idx-1]}")
        )
    
    nav_buttons.append(
        InlineKeyboardButton(text="🛒 Купить", callback_data=f"drone_buy_{drone_type}_1")
    )
    
    if current_idx < len(DRONE_TYPES) - 1:
        nav_buttons.append(
            InlineKeyboardButton(text="»", callback_data=f"drone_shop_{DRONE_TYPES[current_idx+1]}")
        )
    
    keyboard.append(nav_buttons)
    
    # Множители
    keyboard.append([
        InlineKeyboardButton(text="x5", callback_data=f"drone_buy_{drone_type}_5"),
        InlineKeyboardButton(text="x10", callback_data=f"drone_buy_{drone_type}_10"),
        InlineKeyboardButton(text="x50", callback_data=f"drone_buy_{drone_type}_50")
    ])
    
    keyboard.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="drone_angar")
    ])
    
    if edit:
        await message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode='HTML'
        )
    else:
        await message.answer(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode='HTML'
        )


# ==================== ПОКУПКА ДРОНОВ ====================

@router.callback_query(F.data.startswith('drone_buy_'))
async def on_drone_buy(callback: CallbackQuery):
    """Покупка дронов"""
    parts = callback.data.split('_')
    drone_type = parts[2]
    count = int(parts[3])
    
    result = await db.buy_drone(callback.from_user.id, drone_type, count)
    
    if result['success']:
        bought = result['count']
        await callback.answer(f"✅ Куплено дронов: {bought}", show_alert=True)
        # Обновляем магазин
        await show_shop_drone(callback.message, callback.from_user.id, drone_type, edit=True)
    else:
        await callback.answer(f"❌ {result['error']}", show_alert=True)


# ==================== НАЙМ ДРОНОВ ====================

@router.callback_query(F.data.startswith('drone_hire_'))
async def on_drone_hire_menu(callback: CallbackQuery):
    """Меню найма дронов"""
    parts = callback.data.split('_')
    drone_type = parts[2]
    level = int(parts[3])
    
    user_id = callback.from_user.id
    drones_data = await db.get_user_drones(user_id)
    user = await db.get_user(user_id)
    
    config = DRONE_CONFIG.get(drone_type)
    income = DroneSystem.get_income(drone_type, level)
    available = drones_data.get(f"{drone_type}_lvl{level}", 0)
    drones_hired = user.get('drones_hired', 0) if user else 0
    free_slots = MAX_HIRED_DRONES - drones_hired
    
    # Формируем текст дохода
    income_parts = []
    if income['metal'] > 0:
        income_parts.append(f"+{income['metal']} ⚙️")
    if income['crystals'] > 0:
        income_parts.append(f"+{income['crystals']} 💎")
    if income['dark_matter'] > 0:
        income_parts.append(f"+{income['dark_matter']} 🕳️")
    income_text = " ".join(income_parts)
    
    emoji = DroneSystem.get_level_emoji(level)
    
    text = (
        f"🤚 <b>Найм дрона:</b>\n"
        f"{emoji} {config['name']}\n"
        f"▸ Уровень: {level}\n"
        f"▸ Доход: {income_text}\n\n"
        f"Доступно: {available}\n"
        f"Свободных слотов: {free_slots}"
    )
    
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Нанять", callback_data=f"drone_hire_do_{drone_type}_{level}_1")
        ],
        [
            InlineKeyboardButton(text="x5", callback_data=f"drone_hire_do_{drone_type}_{level}_5"),
            InlineKeyboardButton(text="x10", callback_data=f"drone_hire_do_{drone_type}_{level}_10"),
            InlineKeyboardButton(text="Всё", callback_data=f"drone_hire_do_{drone_type}_{level}_all")
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data=f"drone_card_{drone_type}_{level}")
        ]
    ]
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data.startswith('drone_hire_do_'))
async def on_drone_hire_do(callback: CallbackQuery):
    """Выполнить найм"""
    parts = callback.data.split('_')
    drone_type = parts[3]
    level = int(parts[4])
    count_str = parts[5]
    
    user_id = callback.from_user.id
    
    if count_str == 'all':
        # Найм всех доступных
        drones_data = await db.get_user_drones(user_id)
        user = await db.get_user(user_id)
        available = drones_data.get(f"{drone_type}_lvl{level}", 0)
        drones_hired = user.get('drones_hired', 0) if user else 0
        free_slots = MAX_HIRED_DRONES - drones_hired
        count = min(available, free_slots)
    else:
        count = int(count_str)
    
    result = await db.hire_drone(user_id, drone_type, level, count)
    
    if result['success']:
        hired = result['count']
        await callback.answer(f"✅ Нанято дронов: {hired}", show_alert=True)
        # Возвращаемся к карточке
        await on_drone_card(callback)
    else:
        await callback.answer(f"❌ {result['error']}", show_alert=True)


# ==================== ПРОДАЖА ДРОНОВ ====================

@router.callback_query(F.data.startswith('drone_sell_'))
async def on_drone_sell_menu(callback: CallbackQuery):
    """Меню продажи дронов"""
    parts = callback.data.split('_')
    drone_type = parts[2]
    level = int(parts[3])
    
    user_id = callback.from_user.id
    drones_data = await db.get_user_drones(user_id)
    
    config = DRONE_CONFIG.get(drone_type)
    available = drones_data.get(f"{drone_type}_lvl{level}", 0)
    sell_price = DroneSystem.get_sell_price(drone_type, level)
    
    # Формируем текст цены
    price_parts = []
    if sell_price['metal'] > 0:
        price_parts.append(f"{sell_price['metal']:,} ⚙️")
    if sell_price['crystals'] > 0:
        price_parts.append(f"{sell_price['crystals']:,} 💎")
    if sell_price['dark_matter'] > 0:
        price_parts.append(f"{sell_price['dark_matter']:,} 🕳️")
    price_text = " + ".join(price_parts) if price_parts else "0"
    
    emoji = DroneSystem.get_level_emoji(level)
    
    text = (
        f"💰 <b>Продажа дрона:</b>\n"
        f"{emoji} {config['name']}\n"
        f"▸ Количество: {available}\n"
        f"▸ Цена: {price_text} за 1 дрон (30%)"
    )
    
    keyboard = [
        [
            InlineKeyboardButton(text="💰 Продать", callback_data=f"drone_sell_do_{drone_type}_{level}_1")
        ],
        [
            InlineKeyboardButton(text="x5", callback_data=f"drone_sell_do_{drone_type}_{level}_5"),
            InlineKeyboardButton(text="x10", callback_data=f"drone_sell_do_{drone_type}_{level}_10"),
            InlineKeyboardButton(text="Всё", callback_data=f"drone_sell_do_{drone_type}_{level}_all")
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data=f"drone_card_{drone_type}_{level}")
        ]
    ]
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data.startswith('drone_sell_do_'))
async def on_drone_sell_do(callback: CallbackQuery):
    """Выполнить продажу"""
    parts = callback.data.split('_')
    drone_type = parts[3]
    level = int(parts[4])
    count_str = parts[5]
    
    user_id = callback.from_user.id
    
    if count_str == 'all':
        drones_data = await db.get_user_drones(user_id)
        count = drones_data.get(f"{drone_type}_lvl{level}", 0)
    else:
        count = int(count_str)
    
    result = await db.sell_drone(user_id, drone_type, level, count)
    
    if result['success']:
        sold = result['count']
        reward = result['reward']
        reward_text = f"{reward['metal']:,} ⚙️, {reward['crystals']:,} 💎, {reward['dark_matter']:,} 🕳️"
        await callback.answer(f"✅ Продано: {sold}. Получено: {reward_text}", show_alert=True)
        # Возвращаемся к карточке
        await on_drone_card(callback)
    else:
        await callback.answer(f"❌ {result['error']}", show_alert=True)


# ==================== УЛУЧШЕНИЕ ДРОНОВ ====================

@router.callback_query(F.data.startswith('drone_upgrade_menu_'))
async def on_drone_upgrade_menu(callback: CallbackQuery):
    """Меню улучшения дронов"""
    parts = callback.data.split('_')
    drone_type = parts[3]
    level = int(parts[4])
    
    user_id = callback.from_user.id
    drones_data = await db.get_user_drones(user_id)
    
    config = DRONE_CONFIG.get(drone_type)
    available = drones_data.get(f"{drone_type}_lvl{level}", 0)
    
    # Доходы
    current_income = DroneSystem.get_income(drone_type, level)
    next_income = DroneSystem.get_income(drone_type, level + 1) if level < MAX_DRONE_LEVEL else None
    
    emoji = DroneSystem.get_level_emoji(level)
    next_emoji = DroneSystem.get_level_emoji(level + 1) if level < MAX_DRONE_LEVEL else None
    
    text = (
        f"⭐️ <b>Улучшение дрона:</b>\n"
        f"{emoji} {config['name']}\n"
        f"▸ Имеется: {available}\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"После улучшения:\n"
        f"{next_emoji} Уровень: {level + 1}\n"
    )
    
    # Сравнение доходов
    if next_income:
        income_changes = []
        if current_income['metal'] > 0 or next_income['metal'] > 0:
            income_changes.append(f"▸ Доход: {current_income['metal']} ➜ {next_income['metal']} ⚙️")
        if current_income['crystals'] > 0 or next_income['crystals'] > 0:
            income_changes.append(f"▸ Доход: {current_income['crystals']} ➜ {next_income['crystals']} 💎")
        if current_income['dark_matter'] > 0 or next_income['dark_matter'] > 0:
            income_changes.append(f"▸ Доход: {current_income['dark_matter']} ➜ {next_income['dark_matter']} 🕳️")
        
        text += "\n".join(income_changes) + "\n"
    
    current_slots = DroneSystem.get_module_slots(level)
    next_slots = DroneSystem.get_module_slots(level + 1) if level < MAX_DRONE_LEVEL else current_slots
    text += f"▸ Слотов модулей: {current_slots} ➜ {next_slots} 🧩"
    
    max_upgrades = available // 5
    
    keyboard = [
        [
            InlineKeyboardButton(text="⭐️ Улучшить", callback_data=f"drone_upgrade_do_{drone_type}_{level}_1")
        ]
    ]
    
    if max_upgrades >= 5:
        keyboard.append([
            InlineKeyboardButton(text="x5", callback_data=f"drone_upgrade_do_{drone_type}_{level}_5"),
            InlineKeyboardButton(text="x10", callback_data=f"drone_upgrade_do_{drone_type}_{level}_10"),
            InlineKeyboardButton(text="Все", callback_data=f"drone_upgrade_do_{drone_type}_{level}_all")
        ])
    elif max_upgrades >= 1:
        keyboard.append([
            InlineKeyboardButton(text="Все", callback_data=f"drone_upgrade_do_{drone_type}_{level}_all")
        ])
    
    keyboard.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data=f"drone_card_{drone_type}_{level}")
    ])
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data.startswith('drone_upgrade_do_'))
async def on_drone_upgrade_do(callback: CallbackQuery):
    """Выполнить улучшение"""
    parts = callback.data.split('_')
    drone_type = parts[3]
    level = int(parts[4])
    count_str = parts[5]
    
    user_id = callback.from_user.id
    
    if count_str == 'all':
        drones_data = await db.get_user_drones(user_id)
        available = drones_data.get(f"{drone_type}_lvl{level}", 0)
        count = available // 5
    else:
        count = int(count_str)
    
    result = await db.upgrade_drone(user_id, drone_type, level, count)
    
    if result['success']:
        upgraded = result['count']
        await callback.answer(f"✅ Улучшено дронов: {upgraded}", show_alert=True)
        # Переходим к карточке следующего уровня
        await on_drone_card(callback)
    else:
        await callback.answer(f"❌ {result['error']}", show_alert=True)


@router.callback_query(F.data == 'drone_upgrade_all')
async def on_drone_upgrade_all(callback: CallbackQuery):
    """Улучшить все дроны (премиум)"""
    user_id = callback.from_user.id
    
    result = await db.upgrade_all_drones(user_id)
    
    if result['success']:
        upgraded = result['upgraded']
        await callback.answer(f"✅ Улучшено дронов: {upgraded}", show_alert=True)
        await on_drone_types(callback)
    else:
        await callback.answer(f"❌ {result['error']}", show_alert=True)


# ==================== ОТПРАВКА И СБОР ====================

@router.callback_query(F.data == 'drone_send')
async def on_drone_send(callback: CallbackQuery):
    """Отправить дронов на миссию"""
    user_id = callback.from_user.id
    
    result = await db.send_drones_to_mission(user_id)
    
    if result['success']:
        drones_sent = result['drones_sent']
        await callback.answer(f"🚀 Отправлено дронов: {drones_sent}. Миссия: 2 часа", show_alert=True)
        await show_angar(callback.message, user_id, edit=True)
    else:
        await callback.answer(f"❌ {result['error']}", show_alert=True)


@router.callback_query(F.data == 'drone_collect')
async def on_drone_collect(callback: CallbackQuery):
    """Собрать ресурсы из хранилища"""
    user_id = callback.from_user.id
    
    result = await db.collect_drone_storage(user_id)
    
    if result['success']:
        collected = result['collected']
        if result.get('was_cleared'):
            await callback.answer("❌ Ресурсы сгорели (прошло более 24 часов)", show_alert=True)
        else:
            text = f"✅ Собрано:\n⚙️ {collected['metal']:,}\n💎 {collected['crystals']:,}\n🕳️ {collected['dark_matter']:,}"
            await callback.answer(text, show_alert=True)
        await show_angar(callback.message, user_id, edit=True)
    else:
        await callback.answer(f"❌ {result['error']}", show_alert=True)


@router.callback_query(F.data == 'back_to_hangar')
async def on_back_to_hangar(callback: CallbackQuery):
    await show_drones_screen(callback.message, callback.from_user.id, edit=True)
    await callback.answer()


@router.callback_query(F.data == 'back_to_menu')
async def on_back_to_menu(callback: CallbackQuery):
    from handlers.start import welcome_back_user
    user = await db.get_user(callback.from_user.id)
    await welcome_back_user(callback.message, user)
    await callback.answer()
