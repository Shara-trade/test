"""
Handler системы модулей
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db

router = Router()

# Редкость
RARITY_EMOJI = {
    "relic": "⚜️",
    "legendary": "💛",
    "epic": "💜",
    "rare": "🔸",
    "common": "🔹"
}

RARITY_NAMES = {
    "relic": "Реликтовая",
    "legendary": "Легендарная",
    "epic": "Эпическая",
    "rare": "Редкая",
    "common": "Обычная"
}


@router.message(F.text == '⚙️ Модули')
async def cmd_modules(message: Message):
    await show_modules_screen(message, message.from_user.id)


async def show_modules_screen(message_or_callback, user_id: int, edit: bool = False):
    """Главный экран модулей"""
    from aiogram.types import Message
    
    # Получаем информацию о слотах
    slots_info = await db.get_module_slots_info(user_id)
    
    # Получаем установленные модули
    installed_modules = await db.get_installed_modules(user_id, 'player')
    
    # Получаем доступные модули
    available_modules = await db.get_available_modules(user_id)
    
    # Формируем текст
    player_slots = slots_info["player_slots"]
    level = slots_info["level"]
    
    text = '⚙️ <b>СИСТЕМА МОДУЛЕЙ</b>\n\n'
    
    # Слоты игрока
    text += f'👤 <b>На игроке</b> ({player_slots["installed"]}/{player_slots["max"]} слотов)\n'
    
    if not installed_modules:
        text += '  📭 Модули не установлены\n'
    else:
        for module in installed_modules:
            icon = module.get('icon', '⚙️')
            name = module.get('name', 'Модуль')
            slot = module.get('slot_number', 1)
            rarity = module.get('rarity', 'common')
            rarity_emoji = RARITY_EMOJI.get(rarity, '🔹')
            
            # Эффекты
            effects_text = format_effects(module.get('effects', '{}'))
            
            text += f'  [{slot}] {icon} {name} {rarity_emoji}\n'
            if effects_text:
                text += f'      {effects_text}\n'
    
    # Пустые слоты
    empty_slots = player_slots["max"] - player_slots["installed"]
    if empty_slots > 0:
        for i in range(empty_slots):
            slot_num = player_slots["installed"] + i + 1
            # Проверяем, открыт ли слот
            slot_required_level = (slot_num - 3) * 10 if slot_num > 3 else 0
            
            if slot_required_level > level:
                text += f'  [{slot_num}] 🔒 Требуется уровень {slot_required_level}\n'
            else:
                text += f'  [{slot_num}] 🔓 Пустой слот\n'
    
    # Модули на дронах
    drones_info = slots_info.get("drones", [])
    if drones_info:
        text += '\n🤖 <b>На дронах:</b>\n'
        
        for drone in drones_info:
            drone_type = drone.get('drone_type', 'basic')
            max_slots = drone.get('module_slots', 1)
            installed = drone.get('installed', 0)
            drone_id = drone.get('drone_id')
            
            drone_names = {
                'basic': 'Базовый',
                'miner': 'Шахтёр',
                'laser': 'Лазерный',
                'quantum': 'Квантовый',
                'ai': 'ИИ-дрон'
            }
            name = drone_names.get(drone_type, drone_type)
            
            text += f'  {name} #{drone_id}: {installed}/{max_slots}\n'
    
    # Инвентарь модулей
    text += f'\n📦 <b>В инвентаре:</b> {len(available_modules)} модулей\n'
    
    # Клавиатура
    keyboard_buttons = []
    
    if available_modules and player_slots["available"] > 0:
        keyboard_buttons.append([
            InlineKeyboardButton(text='📦 Установить модуль', callback_data='modules_install')
        ])
    
    if installed_modules:
        keyboard_buttons.append([
            InlineKeyboardButton(text='🔧 Снять модуль', callback_data='modules_uninstall')
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text='📊 Бонусы', callback_data='modules_bonuses')
    ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text='◀️ В меню', callback_data='back_to_menu_from_modules')
    ])
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    if edit and isinstance(message_or_callback, Message):
        try:
            await message_or_callback.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
        except:
            await message_or_callback.answer(text, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await message_or_callback.answer(text, reply_markup=reply_markup, parse_mode='HTML')


def format_effects(effects_str: str) -> str:
    """Форматировать эффекты модуля"""
    import json
    
    if not effects_str or effects_str == '{}':
        return ''
    
    try:
        effects = json.loads(effects_str) if isinstance(effects_str, str) else effects_str
        
        effect_names = {
            'mining_bonus': '⛏ Добыча',
            'max_energy': '⚡ Энергия',
            'crit_chance': '💥 Крит',
            'loot_chance': '⭐ Лут',
            'drone_power': '🤖 Дроны',
            'heat_reduction': '🌡 Перегрев',
            'energy_regen': '⚡ Реген',
            'tick_reduction': '⏱ Скорость'
        }
        
        parts = []
        for key, value in effects.items():
            name = effect_names.get(key, key)
            
            if isinstance(value, float) and value < 1:
                parts.append(f'{name} +{int(value * 100)}%')
            else:
                parts.append(f'{name} +{value}')
        
        return ', '.join(parts)
    except:
        return ''


@router.callback_query(F.data == 'modules_install')
async def on_install_menu(callback: CallbackQuery):
    """Меню установки модулей"""
    user_id = callback.from_user.id
    
    # Получаем доступные модули
    available_modules = await db.get_available_modules(user_id)
    
    if not available_modules:
        await callback.answer('Нет доступных модулей для установки', show_alert=True)
        return
    
    # Получаем информацию о слотах
    slots_info = await db.get_module_slots_info(user_id)
    player_slots = slots_info["player_slots"]
    
    text = '📦 <b>ВЫБЕРИТЕ МОДУЛЬ</b>\n\n'
    text += f'Свободных слотов: {player_slots["available"]}\n\n'
    
    keyboard_buttons = []
    
    for i, module in enumerate(available_modules[:8]):  # Максимум 8 кнопок
        icon = module.get('icon', '⚙️')
        name = module.get('name', 'Модуль')[:15]
        rarity = module.get('rarity', 'common')
        rarity_emoji = RARITY_EMOJI.get(rarity, '🔹')
        item_key = module.get('item_key', '')
        
        effects_text = format_effects(module.get('effects', '{}'))
        
        text += f'{icon} <b>{name}</b> {rarity_emoji}\n'
        if effects_text:
            text += f'   {effects_text}\n'
        
        # Используем другой разделитель для item_key с подчёркиваниями
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f'{icon} {name}',
                callback_data=f'module_select:{item_key}'
            )
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text='◀️ Назад', callback_data='modules_back')
    ])
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
    await callback.answer()


@router.callback_query(F.data.startswith('module_select:'))
async def on_module_select(callback: CallbackQuery):
    """Выбор места установки модуля"""
    # Используем : как разделитель: module_select:item_key
    parts = callback.data.split(':', 1)
    item_key = parts[1] if len(parts) > 1 else ''
    user_id = callback.from_user.id
    
    # Получаем информацию о модуле
    modules = await db.get_available_modules(user_id)
    module = next((m for m in modules if m['item_key'] == item_key), None)
    
    if not module:
        await callback.answer('Модуль не найден', show_alert=True)
        return
    
    icon = module.get('icon', '⚙️')
    name = module.get('name', 'Модуль')
    
    text = f'{icon} <b>{name}</b>\n\n'
    text += 'Куда установить?\n'
    
    keyboard_buttons = []
    
    # Получаем слоты
    slots_info = await db.get_module_slots_info(user_id)
    player_slots = slots_info["player_slots"]
    
    # На игрока - используем : как разделитель
    if player_slots["available"] > 0:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f'👤 На игрока ({player_slots["installed"]}/{player_slots["max"]})',
                callback_data=f'module_install:{item_key}:player'
            )
        ])
    
    # На дронов - используем : как разделитель
    for drone in slots_info.get("drones", []):
        drone_id = drone.get('drone_id')
        installed = drone.get('installed', 0)
        max_slots = drone.get('module_slots', 1)
        drone_type = drone.get('drone_type', 'basic')
        
        if installed < max_slots:
            drone_names = {
                'basic': 'Базовый',
                'miner': 'Шахтёр',
                'laser': 'Лазерный',
                'quantum': 'Квантовый',
                'ai': 'ИИ-дрон'
            }
            name_drone = drone_names.get(drone_type, drone_type)
            
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f'🤖 {name_drone} #{drone_id} ({installed}/{max_slots})',
                    callback_data=f'module_install:{item_key}:drone:{drone_id}'
                )
            ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text='❌ Отмена', callback_data='modules_install')
    ])
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
    await callback.answer()


@router.callback_query(F.data.startswith('module_install:'))
async def on_module_install(callback: CallbackQuery):
    """Установка модуля"""
    import logging
    logger = logging.getLogger("modules")
    
    # Используем : как разделитель: module_install:item_key:target[:drone_id]
    parts = callback.data.split(':')
    item_key = parts[1]
    target = parts[2]
    drone_id = parts[3] if len(parts) > 3 else None
    
    user_id = callback.from_user.id
    
    logger.info(f"[on_module_install] User {user_id} installing '{item_key}' to {target}, drone_id={drone_id}")
    
    # Определяем цель
    if target == 'drone' and drone_id:
        install_target = drone_id
    else:
        install_target = 'player'
    
    logger.info(f"[on_module_install] Install target: {install_target}")
    
    # Устанавливаем
    result = await db.install_module(user_id, item_key, install_target, 1)
    
    logger.info(f"[on_module_install] Result: {result}")
    
    if result.get('success'):
        await callback.answer('✅ Модуль установлен!', show_alert=False)
    else:
        error = result.get('error', 'Unknown error')
        logger.error(f"[on_module_install] Failed for user {user_id}: {error}")
        await callback.answer(f'❌ Ошибка: {error}', show_alert=True)
    
    # Возвращаемся
    await show_modules_screen(callback.message, user_id, edit=True)


@router.callback_query(F.data == 'modules_uninstall')
async def on_uninstall_menu(callback: CallbackQuery):
    """Меню снятия модулей"""
    user_id = callback.from_user.id
    
    # Получаем установленные модули
    installed = await db.get_installed_modules(user_id, 'player')
    
    if not installed:
        await callback.answer('Нет установленных модулей', show_alert=True)
        return
    
    text = '🔧 <b>ВЫБЕРИТЕ МОДУЛЬ ДЛЯ СНЯТИЯ</b>\n\n'
    
    keyboard_buttons = []
    
    for module in installed:
        icon = module.get('icon', '⚙️')
        name = module.get('name', 'Модуль')[:15]
        item_key = module.get('item_key', '')
        installed_in = module.get('installed_in', 'player')
        
        if installed_in == 'player':
            location = '👤 Игрок'
        else:
            location = f'🤖 Дрон #{installed_in}'
        
        text += f'{icon} {name} ({location})\n'
        
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f'{icon} {name} - {location}',
                callback_data=f'module_uninstall:{item_key}'
            )
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text='◀️ Назад', callback_data='modules_back')
    ])
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
    await callback.answer()


@router.callback_query(F.data.startswith('module_uninstall:'))
async def on_module_uninstall(callback: CallbackQuery):
    """Снятие модуля"""
    item_key = callback.data.split(':', 1)[-1]
    user_id = callback.from_user.id
    
    result = await db.uninstall_module(user_id, item_key)
    
    if result.get('success'):
        await callback.answer('✅ Модуль снят и возвращён в инвентарь', show_alert=False)
    else:
        await callback.answer(f'❌ Ошибка: {result.get("error")}', show_alert=True)
    
    # Возвращаемся
    await show_modules_screen(callback.message, user_id, edit=True)


@router.callback_query(F.data == 'modules_bonuses')
async def on_bonuses(callback: CallbackQuery):
    """Показать бонусы от модулей"""
    user_id = callback.from_user.id
    
    # Получаем бонусы
    bonuses = await db.get_module_bonuses(user_id)
    
    text = '📊 <b>БОНУСЫ ОТ МОДУЛЕЙ</b>\n\n'
    
    if not bonuses:
        text += '📭 Активных бонусов нет\n'
    else:
        effect_names = {
            'mining_bonus': '⛏ Добыча',
            'max_energy': '⚡ Макс. энергия',
            'crit_chance': '💥 Шанс крита',
            'loot_chance': '⭐ Шанс лута',
            'drone_power': '🤖 Сила дронов',
            'heat_reduction': '🌡 Снижение перегрева',
            'energy_regen': '⚡ Регенерация энергии',
            'tick_reduction': '⏱ Скорость дронов'
        }
        
        for key, value in bonuses.items():
            name = effect_names.get(key, key)
            
            if isinstance(value, float) and value < 1:
                text += f'{name}: +{int(value * 100)}%\n'
            else:
                text += f'{name}: +{value}\n'
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='◀️ Назад', callback_data='modules_back')]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
    await callback.answer()


@router.callback_query(F.data == 'modules_back')
async def on_back(callback: CallbackQuery):
    """Вернуться к модулям"""
    await show_modules_screen(callback.message, callback.from_user.id, edit=True)
    await callback.answer()


@router.callback_query(F.data == 'back_to_menu_from_modules')
async def on_back_to_menu(callback: CallbackQuery):
    """Вернуться в меню"""
    from handlers.start import welcome_back_user
    user = await db.get_user(callback.from_user.id)
    await welcome_back_user(callback.message, user)
    await callback.answer()
