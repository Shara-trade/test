"""
Handler инвентаря и контейнеров
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import math

from database import db

router = Router()

# Пагинация
ITEMS_PER_PAGE = 8

# Редкость
RARITY_ORDER = {
    "relic": 5,
    "legendary": 4,
    "epic": 3,
    "rare": 2,
    "common": 1
}

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

CONTAINER_NAMES = {
    "common": "📦 Обычный",
    "rare": "💎 Редкий",
    "epic": "💜 Эпический",
    "legendary": "💛 Легендарный"
}


@router.message(Command('inventory'))
@router.message(F.text == '📦 Инвентарь')
async def cmd_inventory(message: Message):
    await show_inventory(message, message.from_user.id)


async def show_inventory(message_or_callback, user_id: int, page: int = 1, edit: bool = False):
    """Показать инвентарь с пагинацией"""
    from aiogram.types import Message
    
    # Получаем инвентарь
    items = await db.get_user_inventory(user_id)
    
    if not items:
        text = (
            '📦 <b>ИНВЕНТАРЬ</b>\n\n'
            '🎒 Ваш инвентарь пуст!\n\n'
            '💡 Добывайте ресурсы, открывайте контейнеры\n'
            'и находите редкие предметы!'
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='🎁 Контейнеры', callback_data='containers')],
            [InlineKeyboardButton(text='◀️ В меню', callback_data='back_to_menu_from_inventory')]
        ])
        
        if edit and isinstance(message_or_callback, Message):
            try:
                await message_or_callback.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
            except:
                await message_or_callback.answer(text, reply_markup=keyboard, parse_mode='HTML')
        else:
            await message_or_callback.answer(text, reply_markup=keyboard, parse_mode='HTML')
        return
    
    # Сортируем по редкости
    sorted_items = sorted(items, key=lambda x: RARITY_ORDER.get(x.get('rarity', 'common'), 0), reverse=True)
    
    # Пагинация
    total_pages = math.ceil(len(sorted_items) / ITEMS_PER_PAGE)
    page = max(1, min(page, total_pages))
    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    page_items = sorted_items[start_idx:end_idx]
    
    # Формируем текст
    text = f'📦 <b>ИНВЕНТАРЬ</b>\n'
    text += f'<i>Страница {page}/{total_pages} • Всего: {len(sorted_items)} предметов</i>\n\n'
    
    current_rarity = None
    for item in page_items:
        rarity = item.get('rarity', 'common')
        
        # Заголовок группы
        if rarity != current_rarity:
            current_rarity = rarity
            emoji = RARITY_EMOJI.get(rarity, '🔹')
            name = RARITY_NAMES.get(rarity, 'Обычная')
            text += f'\n{emoji} <b>{name}</b>\n'
        
        # Предмет
        item_name = item.get('name', 'Неизвестно')
        quantity = item.get('quantity', 1)
        icon = item.get('icon', '📦')
        
        text += f'  {icon} {item_name} x{quantity}\n'
    
    # Клавиатура
    keyboard_buttons = []
    
    # Кнопки предметов (по 2 в ряд)
    row = []
    for item in page_items:
        item_key = item.get('item_key', '')
        item_name = item.get('name', '?')[:12]
        quantity = item.get('quantity', 1)
        row.append(InlineKeyboardButton(
            text=f'{item_name} x{quantity}',
            callback_data=f'item_info_{item_key}'
        ))
        if len(row) == 2:
            keyboard_buttons.append(row)
            row = []
    
    if row:
        keyboard_buttons.append(row)
    
    # Навигация
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text='◀️', callback_data=f'inv_page_{page-1}'))
    nav_buttons.append(InlineKeyboardButton(text=f'{page}/{total_pages}', callback_data='inv_page_info'))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text='▶️', callback_data=f'inv_page_{page+1}'))
    
    if len(nav_buttons) > 1:
        keyboard_buttons.append(nav_buttons)
    
    # Основные кнопки
    keyboard_buttons.append([
        InlineKeyboardButton(text='🎁 Контейнеры', callback_data='containers'),
        InlineKeyboardButton(text='📊 Статистика', callback_data='inv_stats')
    ])
    keyboard_buttons.append([
        InlineKeyboardButton(text='◀️ В меню', callback_data='back_to_menu_from_inventory')
    ])
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    if edit and isinstance(message_or_callback, Message):
        try:
            await message_or_callback.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
        except:
            await message_or_callback.answer(text, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await message_or_callback.answer(text, reply_markup=reply_markup, parse_mode='HTML')


@router.callback_query(F.data.startswith('inv_page_'))
async def on_inventory_page(callback: CallbackQuery):
    """Пагинация инвентаря"""
    page = int(callback.data.split('_')[-1])
    await show_inventory(callback.message, callback.from_user.id, page=page, edit=True)
    await callback.answer()


@router.callback_query(F.data == 'inv_page_info')
async def on_page_info(callback: CallbackQuery):
    await callback.answer('Используйте стрелки для навигации', show_alert=False)


@router.callback_query(F.data.startswith('item_info_'))
async def on_item_info(callback: CallbackQuery):
    """Детальная информация о предмете"""
    item_key = callback.data.replace('item_info_', '')
    user_id = callback.from_user.id
    
    # Получаем предмет
    item = await db.get_user_item(user_id, item_key)
    
    if not item:
        await callback.answer('Предмет не найден', show_alert=True)
        return
    
    name = item.get('name', 'Неизвестно')
    description = item.get('description', 'Описание отсутствует')
    rarity = item.get('rarity', 'common')
    item_type = item.get('item_type', 'resource')
    effects = item.get('effects', '{}')
    can_sell = item.get('can_sell', 1)
    base_price = item.get('base_price', 0)
    quantity = item.get('quantity', 1)
    level_required = item.get('level_required', 1)
    icon = item.get('icon', '📦')
    
    rarity_emoji = RARITY_EMOJI.get(rarity, '🔹')
    rarity_name = RARITY_NAMES.get(rarity, 'Обычная')
    
    # Формируем текст
    text = (
        f'{icon} <b>{name}</b>\n\n'
        f'▸ Количество: x{quantity}\n'
        f'▸ Редкость: {rarity_emoji} {rarity_name}\n'
        f'▸ Тип: {item_type}\n'
    )
    
    if level_required > 1:
        text += f'▸ Требуемый уровень: {level_required}\n'
    
    text += f'\n📝 <b>Описание:</b>\n{description}\n'
    
    # Эффекты
    if effects and effects != '{}':
        import json
        try:
            effects_dict = json.loads(effects) if isinstance(effects, str) else effects
            if effects_dict:
                text += '\n✨ <b>Эффекты:</b>\n'
                for key, value in effects_dict.items():
                    # Красивые названия эффектов
                    effect_names = {
                        'mining_bonus': '⛏ Добыча',
                        'max_energy': '⚡ Макс. энергия',
                        'crit_chance': '💥 Шанс крита',
                        'loot_chance': '⭐ Шанс лута',
                        'drone_power': '🤖 Сила дронов',
                        'heat_reduction': '🌡 Снижение перегрева',
                        'tick_reduction': '⏱ Скорость дронов'
                    }
                    effect_name = effect_names.get(key, key)
                    
                    if isinstance(value, float) and value < 1:
                        text += f'  ▸ {effect_name}: +{int(value * 100)}%\n'
                    else:
                        text += f'  ▸ {effect_name}: +{value}\n'
        except:
            pass
    
    if can_sell:
        total_price = base_price * quantity
        text += f'\n💰 <b>Цена:</b> {base_price:,} кредитов (всего: {total_price:,})'
    
    # Клавиатура
    keyboard_buttons = []
    
    # Действия по типу
    if item_type in ['consumable', 'boost']:
        keyboard_buttons.append([
            InlineKeyboardButton(text='✅ Использовать', callback_data=f'use_item_{item_key}')
        ])
    
    if can_sell and base_price > 0:
        keyboard_buttons.append([
            InlineKeyboardButton(text='💰 Продать x1', callback_data=f'sell_item_{item_key}_1'),
            InlineKeyboardButton(text='💰 Продать все', callback_data=f'sell_item_{item_key}_all')
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text='◀️ Назад', callback_data='inv_page_1')
    ])
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
    except:
        await callback.message.answer(text, reply_markup=reply_markup, parse_mode='HTML')
    
    await callback.answer()


@router.callback_query(F.data.startswith('use_item_'))
async def on_use_item(callback: CallbackQuery):
    """Использовать предмет"""
    item_key = callback.data.replace('use_item_', '')
    user_id = callback.from_user.id
    
    item = await db.get_user_item(user_id, item_key)
    
    if not item:
        await callback.answer('Предмет не найден', show_alert=True)
        return
    
    effects = item.get('effects', '{}')
    item_name = item.get('name', 'Предмет')
    
    import json
    try:
        effects_dict = json.loads(effects) if isinstance(effects, str) else effects
        
        # Применяем эффекты
        updates = {}
        
        if 'max_energy' in effects_dict:
            updates['max_energy'] = effects_dict['max_energy']
        
        if 'energy' in effects_dict:
            updates['energy'] = effects_dict['energy']
        
        if updates:
            await db.update_user_resources(user_id, **updates)
        
        # Удаляем предмет
        await db.remove_item(user_id, item_key, 1)
        
        await callback.answer(f'✅ {item_name} использован!', show_alert=True)
        
    except Exception as e:
        await callback.answer(f'Ошибка: {e}', show_alert=True)
        return
    
    # Возвращаемся в инвентарь
    await show_inventory(callback.message, user_id, edit=True)


@router.callback_query(F.data.startswith('sell_item_'))
async def on_sell_item(callback: CallbackQuery):
    """Продать предмет"""
    parts = callback.data.split('_')
    item_key = parts[2]
    sell_type = parts[3] if len(parts) > 3 else '1'
    
    user_id = callback.from_user.id
    
    item = await db.get_user_item(user_id, item_key)
    
    if not item:
        await callback.answer('Предмет не найден', show_alert=True)
        return
    
    if not item.get('can_sell', 1):
        await callback.answer('Этот предмет нельзя продать', show_alert=True)
        return
    
    base_price = item.get('base_price', 0)
    quantity = item.get('quantity', 1)
    item_name = item.get('name', 'Предмет')
    
    if sell_type == 'all':
        sell_quantity = quantity
    else:
        sell_quantity = 1
    
    total_price = base_price * sell_quantity
    
    # Продаём
    await db.update_user_resources(user_id, credits=total_price)
    await db.remove_item(user_id, item_key, sell_quantity)
    
    await callback.answer(f'💰 Продано {item_name} x{sell_quantity} за {total_price:,} кредитов!', show_alert=True)
    
    # Возвращаемся в инвентарь
    await show_inventory(callback.message, user_id, edit=True)


@router.callback_query(F.data == 'inv_stats')
async def on_inventory_stats(callback: CallbackQuery):
    """Статистика инвентаря"""
    user_id = callback.from_user.id
    
    stats = await db.get_inventory_stats(user_id)
    
    total_items = stats.get('total_items', 0)
    total_quantity = stats.get('total_quantity', 0)
    total_value = stats.get('total_value', 0)
    by_rarity = stats.get('by_rarity', {})
    
    text = (
        f'📊 <b>СТАТИСТИКА ИНВЕНТАРЯ</b>\n\n'
        f'📦 Уникальных предметов: {total_items}\n'
        f'📊 Всего единиц: {total_quantity}\n'
        f'💰 Общая стоимость: {total_value:,} кредитов\n\n'
    )
    
    text += '<b>По редкости:</b>\n'
    for rarity in ['relic', 'legendary', 'epic', 'rare', 'common']:
        count = by_rarity.get(rarity, 0)
        if count > 0:
            emoji = RARITY_EMOJI.get(rarity, '🔹')
            name = RARITY_NAMES.get(rarity, 'Обычная')
            text += f'{emoji} {name}: {count}\n'
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='◀️ Назад', callback_data='inv_page_1')]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
    await callback.answer()


# ==================== КОНТЕЙНЕРЫ ====================

@router.callback_query(F.data == 'containers')
async def on_containers(callback: CallbackQuery):
    """Показать контейнеры"""
    await show_containers(callback.message, callback.from_user.id, edit=True)
    await callback.answer()


async def show_containers(message_or_callback, user_id: int, edit: bool = False):
    """Экран контейнеров"""
    from aiogram.types import Message
    from datetime import datetime
    
    # Обновляем статусы
    await db.update_container_status(user_id)
    
    # Получаем контейнеры
    containers = await db.get_user_containers(user_id)
    
    if not containers:
        text = (
            '🎁 <b>КОНТЕЙНЕРЫ</b>\n\n'
            '📦 У вас пока нет контейнеров!\n\n'
            '💡 Контейнеры можно получить:\n'
            '  ▸ При добыче ресурсов\n'
            '  ▸ За выполнение заданий\n'
            '  ▸ В награду за ивенты'
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='◀️ В инвентарь', callback_data='inv_page_1')]
        ])
        
        if edit and isinstance(message_or_callback, Message):
            try:
                await message_or_callback.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
            except:
                await message_or_callback.answer(text, reply_markup=keyboard, parse_mode='HTML')
        else:
            await message_or_callback.answer(text, reply_markup=keyboard, parse_mode='HTML')
        return
    
    text = '🎁 <b>КОНТЕЙНЕРЫ</b>\n\n'
    
    keyboard_buttons = []
    
    for container in containers:
        container_id = container.get('container_id')
        container_type = container.get('container_type', 'common')
        status = container.get('status', 'locked')
        unlock_time_str = container.get('unlock_time')
        
        name = CONTAINER_NAMES.get(container_type, '📦 Контейнер')
        text += f'{name}\n'
        
        if status == 'ready':
            text += '  ✅ <b>Готов к открытию!</b>\n\n'
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f'🔓 Открыть {name}',
                    callback_data=f'open_container_{container_id}'
                )
            ])
        
        elif status == 'locked' and unlock_time_str:
            try:
                if isinstance(unlock_time_str, str):
                    unlock_dt = datetime.fromisoformat(unlock_time_str)
                else:
                    unlock_dt = unlock_time_str
                
                remaining = (unlock_dt - datetime.now()).total_seconds()
                
                if remaining > 0:
                    minutes = int(remaining // 60)
                    seconds = int(remaining % 60)
                    text += f'  ⏳ Откроется через: {minutes}:{seconds:02d}\n\n'
                else:
                    text += '  ✅ <b>Готов к открытию!</b>\n\n'
                    keyboard_buttons.append([
                        InlineKeyboardButton(
                            text=f'🔓 Открыть {name}',
                            callback_data=f'open_container_{container_id}'
                        )
                    ])
            except:
                text += '  ⏳ Заблокирован\n\n'
        else:
            text += '  ⏳ Заблокирован\n\n'
    
    keyboard_buttons.append([
        InlineKeyboardButton(text='◀️ В инвентарь', callback_data='inv_page_1')
    ])
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    if edit and isinstance(message_or_callback, Message):
        try:
            await message_or_callback.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
        except:
            await message_or_callback.answer(text, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await message_or_callback.answer(text, reply_markup=reply_markup, parse_mode='HTML')


@router.callback_query(F.data.startswith('open_container_'))
async def on_open_container(callback: CallbackQuery):
    """Открыть контейнер"""
    container_id = int(callback.data.replace('open_container_', ''))
    user_id = callback.from_user.id
    
    # Открываем
    result = await db.open_container(user_id, container_id)
    
    if not result:
        await callback.answer('Контейнер не найден', show_alert=True)
        return
    
    if not result.get('success'):
        if result.get('error') == 'not_ready':
            await callback.answer('Контейнер ещё не готов', show_alert=True)
        else:
            await callback.answer('Ошибка открытия', show_alert=True)
        return
    
    # Формируем текст с наградами
    text = '🎁 <b>КОНТЕЙНЕР ОТКРЫТ!</b>\n\n'
    text += '✨ Вы получили:\n\n'
    
    rewards = result.get('rewards', [])
    
    for reward in rewards:
        reward_type = reward.get('type')
        
        if reward_type == 'item':
            item_name = reward.get('name', 'Предмет')
            quantity = reward.get('quantity', 1)
            rarity = reward.get('rarity', 'common')
            emoji = RARITY_EMOJI.get(rarity, '🔹')
            text += f'{emoji} {item_name} x{quantity}\n'
        
        elif reward_type == 'resource':
            resource = reward.get('resource')
            quantity = reward.get('quantity', 0)
            
            resource_names = {
                'metal': '⚙️ Металл',
                'crystals': '💎 Кристаллы',
                'dark_matter': '⚫ Тёмная материя',
                'credits': '💵 Кредиты',
                'energy': '⚡ Энергия'
            }
            name = resource_names.get(resource, resource)
            text += f'{name} x{quantity:,}\n'
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🎁 Ещё контейнеры', callback_data='containers')],
        [InlineKeyboardButton(text='📦 В инвентарь', callback_data='inv_page_1')]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
    await callback.answer()


@router.callback_query(F.data == 'back_to_menu_from_inventory')
async def on_back_to_menu(callback: CallbackQuery):
    """Вернуться в меню"""
    from handlers.start import welcome_back_user
    user = await db.get_user(callback.from_user.id)
    await welcome_back_user(callback.message, user)
    await callback.answer()
