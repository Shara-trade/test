"""
Handler инвентаря
Согласно Update.txt - три раздела: Контейнеры, Материалы, Ресурсы
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
import logging
import re

from database import db
from game.materials import MaterialSystem
from game.containers import ContainerSystem
from core.utils import format_number, plural_form

router = Router()
logger = logging.getLogger(__name__)

# Типы контейнеров в порядке отображения
CONTAINER_TYPES = ["common", "rare", "epic", "mythic", "legendary"]

CONTAINER_NAMES = {
    "common": "📦 Обычный",
    "rare": "🎁 Редкий",
    "epic": "💎 Эпический",
    "mythic": "👑 Мифический",
    "legendary": "🔥 Легендарный",
}


# ==================== ГЛАВНОЕ МЕНЮ ИНВЕНТАРЯ ====================

@router.message(Command('inventory'))
@router.message(F.text == '📦 Инвентарь')
async def cmd_inventory(message: Message):
    """Открыть инвентарь"""
    await show_inventory_main(message, message.from_user.id)


async def show_inventory_main(message_or_callback, user_id: int, edit: bool = False):
    """Главное меню инвентаря"""
    from aiogram.types import Message
    
    text = (
        '🎒 <b>Твой космический инвентарь</b>\n\n'
        'Выбери раздел:'
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='📦', callback_data='inv_containers'),
            InlineKeyboardButton(text='🧩', callback_data='inv_materials'),
            InlineKeyboardButton(text='💰', callback_data='inv_resources'),
        ],
        [
            InlineKeyboardButton(text='❌ Закрыть', callback_data='inv_close'),
        ],
    ])
    
    if edit and isinstance(message_or_callback, Message):
        try:
            await message_or_callback.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
        except:
            await message_or_callback.answer(text, reply_markup=keyboard, parse_mode='HTML')
    else:
        await message_or_callback.answer(text, reply_markup=keyboard, parse_mode='HTML')


@router.callback_query(F.data == 'inventory')
async def on_inventory_callback(callback: CallbackQuery):
    """Callback для открытия инвентаря"""
    await show_inventory_main(callback.message, callback.from_user.id, edit=True)
    await callback.answer()


@router.callback_query(F.data == 'inv_close')
async def on_inv_close(callback: CallbackQuery):
    """Закрыть инвентарь"""
    try:
        await callback.message.delete()
    except:
        pass
    await callback.answer()


# ==================== РАЗДЕЛ КОНТЕЙНЕРОВ ====================

@router.callback_query(F.data == 'inv_containers')
async def on_inv_containers(callback: CallbackQuery):
    """Раздел контейнеров"""
    await show_containers_section(callback.message, callback.from_user.id, edit=True)
    await callback.answer()


async def show_containers_section(message_or_callback, user_id: int, edit: bool = False):
    """Показать раздел контейнеров"""
    from aiogram.types import Message
    
    # Получаем количество контейнеров каждого типа
    containers_count = await get_containers_count(user_id)
    
    if not containers_count or sum(containers_count.values()) == 0:
        text = (
            '📦 <b>Контейнеры</b>\n\n'
            'У тебя пока нет контейнеров.\n\n'
            '💡 Контейнеры можно получить при добыче ресурсов!'
        )
    else:
        text = '📦 <b>Контейнеры</b>\n\nТвои контейнеры:\n\n'
        
        for container_type in CONTAINER_TYPES:
            count = containers_count.get(container_type, 0)
            if count > 0:
                name = CONTAINER_NAMES.get(container_type, '📦 Контейнер')
                text += f'▸ {name}: {format_number(count)}\n'
        
        text += (
            '\nЧтобы открыть контейнер, напиши:\n'
            '<code>открыть редкий контейнер</code>\n\n'
            'или коротко:\n'
            '<code>отк ред</code>'
        )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='📦', callback_data='inv_containers'),
            InlineKeyboardButton(text='🧩', callback_data='inv_materials'),
            InlineKeyboardButton(text='💰', callback_data='inv_resources'),
        ],
        [
            InlineKeyboardButton(text='❌ Закрыть', callback_data='inv_close'),
        ],
    ])
    
    if edit and isinstance(message_or_callback, Message):
        try:
            await message_or_callback.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
        except:
            await message_or_callback.answer(text, reply_markup=keyboard, parse_mode='HTML')
    else:
        await message_or_callback.answer(text, reply_markup=keyboard, parse_mode='HTML')


async def get_containers_count(user_id: int) -> dict:
    """Получить количество контейнеров пользователя"""
    # Контейнеры хранятся в инвентаре как предметы с item_key = container_{type}
    result = {}
    
    for container_type in CONTAINER_TYPES:
        item_key = f"container_{container_type}"
        item = await db.get_user_item(user_id, item_key)
        result[container_type] = item.get('quantity', 0) if item else 0
    
    return result


# ==================== РАЗДЕЛ МАТЕРИАЛОВ ====================

@router.callback_query(F.data == 'inv_materials')
async def on_inv_materials(callback: CallbackQuery):
    """Раздел материалов"""
    await show_materials_section(callback.message, callback.from_user.id, edit=True)
    await callback.answer()


async def show_materials_section(message_or_callback, user_id: int, edit: bool = False):
    """Показать раздел материалов"""
    from aiogram.types import Message
    
    # Получаем инвентарь пользователя
    inventory = await db.get_user_inventory(user_id)
    inventory_dict = {item['item_key']: item.get('quantity', 0) for item in inventory}
    
    text = '🧩 <b>Материалы</b>\n\nТвои космические материалы:\n\n'
    
    has_materials = False
    
    for material in MaterialSystem.get_all_materials():
        quantity = inventory_dict.get(material.key, 0)
        if quantity > 0:
            has_materials = True
            text += f'▸ {material.emoji} {material.name}: {format_number(quantity)}\n'
    
    if not has_materials:
        text += 'У тебя пока нет материалов.\n\n'
        text += '💡 Материалы можно получить из контейнеров!'
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='📦', callback_data='inv_containers'),
            InlineKeyboardButton(text='🧩', callback_data='inv_materials'),
            InlineKeyboardButton(text='💰', callback_data='inv_resources'),
        ],
        [
            InlineKeyboardButton(text='❌ Закрыть', callback_data='inv_close'),
        ],
    ])
    
    if edit and isinstance(message_or_callback, Message):
        try:
            await message_or_callback.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
        except:
            await message_or_callback.answer(text, reply_markup=keyboard, parse_mode='HTML')
    else:
        await message_or_callback.answer(text, reply_markup=keyboard, parse_mode='HTML')


# ==================== РАЗДЕЛ РЕСУРСОВ ====================

@router.callback_query(F.data == 'inv_resources')
async def on_inv_resources(callback: CallbackQuery):
    """Раздел ресурсов"""
    await show_resources_section(callback.message, callback.from_user.id, edit=True)
    await callback.answer()


async def show_resources_section(message_or_callback, user_id: int, edit: bool = False):
    """Показать раздел ресурсов"""
    from aiogram.types import Message
    
    # Получаем данные пользователя
    user = await db.get_user(user_id)
    
    if not user:
        text = '❌ Ошибка: пользователь не найден'
    else:
        metal = user.get('metal', 0) or 0
        crystals = user.get('crystals', 0) or 0
        dark_matter = user.get('dark_matter', 0) or 0
        
        text = (
            '💰 <b>Ресурсы</b>\n\n'
            'Твои ресурсы:\n\n'
            f'▸ Металл: {format_number(metal)} ⚙️\n'
            f'▸ Кристаллы: {format_number(crystals)} 💎\n'
            f'▸ Тёмная материя: {format_number(dark_matter)} 🕳️'
        )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='📦', callback_data='inv_containers'),
            InlineKeyboardButton(text='🧩', callback_data='inv_materials'),
            InlineKeyboardButton(text='💰', callback_data='inv_resources'),
        ],
        [
            InlineKeyboardButton(text='❌ Закрыть', callback_data='inv_close'),
        ],
    ])
    
    if edit and isinstance(message_or_callback, Message):
        try:
            await message_or_callback.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
        except:
            await message_or_callback.answer(text, reply_markup=keyboard, parse_mode='HTML')
    else:
        await message_or_callback.answer(text, reply_markup=keyboard, parse_mode='HTML')


# ==================== КОМАНДЫ ОТКРЫТИЯ КОНТЕЙНЕРОВ ====================

# Паттерны для команд открытия
OPEN_PATTERNS = [
    r'^открыть\s+(.+?)\s+контейнер',
    r'^отк\s+(.+)$',
    r'^open\s+(.+?)\s+container',
]

@router.message()
async def on_text_message(message: Message):
    """Обработка текстовых сообщений для открытия контейнеров"""
    text = message.text.lower().strip()
    user_id = message.from_user.id
    
    # Проверяем паттерны
    container_type_text = None
    
    for pattern in OPEN_PATTERNS:
        match = re.match(pattern, text)
        if match:
            container_type_text = match.group(1).strip()
            break
    
    if not container_type_text:
        return  # Не команда открытия
    
    # Определяем тип контейнера
    container_type = ContainerSystem.resolve_container_type(container_type_text)
    
    if not container_type:
        await message.answer(
            '❌ Неизвестный тип контейнера.\n\n'
            'Доступные типы: обычный, редкий, эпический, мифический, легендарный\n\n'
            'Сокращения: обыч, ред, эп, миф, лег'
        )
        return
    
    # Открываем контейнер
    await open_container_by_type(message, user_id, container_type)


async def open_container_by_type(message: Message, user_id: int, container_type: str):
    """Открыть контейнер указанного типа"""
    
    # Проверяем наличие контейнера
    item_key = f"container_{container_type}"
    container_item = await db.get_user_item(user_id, item_key)
    
    if not container_item or container_item.get('quantity', 0) <= 0:
        await message.answer('❌ У тебя нет таких контейнеров')
        return
    
    # Списываем контейнер
    await db.remove_item(user_id, item_key, 1)
    
    # Генерируем награды
    rewards = ContainerSystem.generate_rewards(container_type)
    
    # Выдаём ресурсы
    resources = rewards.get('resources', {})
    if resources:
        await db.update_user_resources(
            user_id,
            metal=resources.get('metal', 0),
            crystals=resources.get('crystals', 0),
            dark_matter=resources.get('dark_matter', 0),
        )
    
    # Выдаём материалы
    materials = rewards.get('materials', {})
    for material_key, amount in materials.items():
        await db.add_item(user_id, material_key, amount)
    
    # Формируем отчёт
    container_name = ContainerSystem.get_container_name(container_type)
    
    text = f'🔥 Ты открыл {container_name.lower()} контейнер!\n\n'
    
    # Ресурсы
    if resources:
        text += '<b>Ресурсы:</b>\n'
        if resources.get('metal', 0) > 0:
            text += f"⚙️ Металл +{format_number(resources['metal'])}\n"
        if resources.get('crystals', 0) > 0:
            text += f"💎 Кристаллы +{format_number(resources['crystals'])}\n"
        if resources.get('dark_matter', 0) > 0:
            text += f"🕳️ Тёмная материя +{format_number(resources['dark_matter'])}\n"
        text += '\n'
    
    # Материалы
    if materials:
        text += '<b>Материалы:</b>\n'
        
        # Сортируем по группам
        from game.materials import MaterialGroup
        
        for group in [MaterialGroup.COMMON, MaterialGroup.RARE, MaterialGroup.EPIC]:
            for material in MaterialSystem.get_materials_by_group(group):
                amount = materials.get(material.key, 0)
                if amount > 0:
                    text += f'{material.emoji} {material.name} +{format_number(amount)}\n'
    
    await message.answer(text, parse_mode='HTML')


# ==================== СТАРЫЕ CALLBACKS ДЛЯ СОВМЕСТИМОСТИ ====================

@router.callback_query(F.data == 'containers')
async def on_containers_legacy(callback: CallbackQuery):
    """Совместимость со старыми вызовами"""
    await show_containers_section(callback.message, callback.from_user.id, edit=True)
    await callback.answer()


@router.callback_query(F.data == 'back_to_menu_from_inventory')
async def on_back_to_menu(callback: CallbackQuery):
    """Вернуться в меню"""
    from handlers.start import welcome_back_user
    user = await db.get_user(callback.from_user.id)
    await welcome_back_user(callback.message, user)
    await callback.answer()
