"""
Handler системы модулей
Согласно module.txt - инвентарь, слоты, улучшение, продажа, разборка
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import random
import logging

from database import db
from game.modules import (
    ModuleSystem, Rarity, RARITY_EMOJI, RARITY_NAME,
    BUFF_NAMES, BUFF_UNITS, DEBUFF_NAMES, DEBUFF_UNITS,
    BUFF_VALUES, DEBUFF_VALUES
)
from core.utils import format_number

router = Router()
logger = logging.getLogger(__name__)

# Константы
MODULES_PER_PAGE = 18  # 3 колонки × 6 строк
MAX_SLOTS = 4  # 3 обычных + 1 привилегированный


# ==================== ГЛАВНОЕ МЕНЮ МОДУЛЕЙ ====================

@router.message(F.text == '⚙️ Модули')
async def cmd_modules(message: Message):
    """Команда /мод или кнопка Модули"""
    await show_modules_inventory(message, message.from_user.id, page=1)


@router.callback_query(F.data == 'modules')
async def on_modules_callback(callback: CallbackQuery):
    """Callback для открытия модулей из Inline-кнопки"""
    await show_modules_inventory(callback.message, callback.from_user.id, page=1, edit=True)
    await callback.answer()


async def show_modules_inventory(message_or_callback, user_id: int, page: int = 1, edit: bool = False):
    """Показать инвентарь модулей"""
    from aiogram.types import Message
    
    # Получаем модули пользователя
    modules = await db.get_user_modules(user_id)
    
    if not modules:
        text = (
            '🧩 <b>Модули</b>\n\n'
            'У тебя пока нет модулей.\n'
            'Получить модули можно из контейнеров (КСМ).'
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='❌ Закрыть', callback_data='modules_close')]
        ])
    
        if edit and isinstance(message_or_callback, Message):
            try:
                await message_or_callback.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
            except:
                await message_or_callback.answer(text, reply_markup=keyboard, parse_mode='HTML')
        else:
            await message_or_callback.answer(text, reply_markup=keyboard, parse_mode='HTML')
        return
    
    # Сортировка: по редкости (от легендарной к обычной), потом по ID
    modules.sort(key=lambda m: (-m.get('rarity', 1), m.get('module_id', 0)))
    
    # Пагинация
    total_pages = max(1, (len(modules) + MODULES_PER_PAGE - 1) // MODULES_PER_PAGE)
    page = max(1, min(page, total_pages))
    
    start_idx = (page - 1) * MODULES_PER_PAGE
    end_idx = start_idx + MODULES_PER_PAGE
    page_modules = modules[start_idx:end_idx]
    
    # Формируем текст
    text = f'🧩 <b>Модули (страница {page}/{total_pages})</b>'
    
    # Формируем кнопки (3 колонки × 6 строк)
    keyboard_buttons = []
    row = []
    
    for module in page_modules:
        rarity = Rarity(module.get('rarity', 1))
        rarity_emoji = RARITY_EMOJI[rarity]
        name = module.get('name', '??-??')
        slot = module.get('slot')
        module_id = module.get('module_id')
        
        # Если модуль надет — добавляем 🤚
        if slot is not None:
            button_text = f"🤚{rarity_emoji} {name}"
        else:
            button_text = f"{rarity_emoji} {name}"
        
        row.append(InlineKeyboardButton(
            text=button_text,
            callback_data=f'module_view:{module_id}'
        ))
        
        if len(row) == 3:
            keyboard_buttons.append(row)
            row = []
    
    if row:
        keyboard_buttons.append(row)
    
    # Навигация
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text='«', callback_data=f'modules_page:{page-1}'))
    nav_row.append(InlineKeyboardButton(text='Слоты', callback_data='modules_slots'))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text='»', callback_data=f'modules_page:{page+1}'))
    
    keyboard_buttons.append(nav_row)
    keyboard_buttons.append([
        InlineKeyboardButton(text='❌ Закрыть', callback_data='modules_close')
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    if edit and isinstance(message_or_callback, Message):
        try:
            await message_or_callback.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
        except:
            await message_or_callback.answer(text, reply_markup=keyboard, parse_mode='HTML')
    else:
        await message_or_callback.answer(text, reply_markup=keyboard, parse_mode='HTML')


@router.callback_query(F.data == 'modules_close')
async def on_modules_close(callback: CallbackQuery):
    """Закрыть инвентарь модулей"""
    try:
        await callback.message.delete()
    except:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith('modules_page:'))
async def on_modules_page(callback: CallbackQuery):
    """Перелистывание страниц"""
    page = int(callback.data.split(':')[1])
    await show_modules_inventory(callback.message, callback.from_user.id, page=page, edit=True)
    await callback.answer()


# ==================== КАРТОЧКА МОДУЛЯ ====================

@router.callback_query(F.data.startswith('module_view:'))
async def on_module_view(callback: CallbackQuery):
    """Просмотр карточки модуля"""
    module_id = int(callback.data.split(':')[1])
    user_id = callback.from_user.id
    
    module = await db.get_module_by_id(user_id, module_id)
    
    if not module:
        await callback.answer('Модуль не найден', show_alert=True)
        return
    
    # Формируем карточку
    text = ModuleSystem.format_module_card(module)
    
    # Кнопки
    rarity = Rarity(module.get('rarity', 1))
    slot = module.get('slot')
    
    keyboard_buttons = []
    
    # 🤚 — установка/снятие
    if slot is not None:
        equip_text = f"🤚 Снять со слота {slot}"
        equip_action = f'module_uninstall_confirm:{module_id}'
    else:
        equip_text = "🤚 Установить"
        equip_action = f'module_select_slot:{module_id}'
    
    keyboard_buttons.append([
        InlineKeyboardButton(text=equip_text, callback_data=equip_action),
        InlineKeyboardButton(text='💰 Продать', callback_data=f'module_sell_confirm:{module_id}'),
    ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text='🗑️ Разобрать', callback_data=f'module_scrap_confirm:{module_id}'),
    ])
    
    # ⭐️ — улучшение (только если не надет и не легендарный)
    if slot is None and rarity < Rarity.LEGENDARY:
        keyboard_buttons.append([
            InlineKeyboardButton(text='⭐️ Улучшить', callback_data=f'module_upgrade:{module_id}')
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text='⬅️ Назад', callback_data='modules_back'),
        InlineKeyboardButton(text='❌ Закрыть', callback_data='modules_close')
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
    await callback.answer()


@router.callback_query(F.data == 'modules_back')
async def on_modules_back(callback: CallbackQuery):
    """Возврат в инвентарь"""
    await show_modules_inventory(callback.message, callback.from_user.id, page=1, edit=True)
    await callback.answer()


# ==================== СИСТЕМА СЛОТОВ ====================

@router.callback_query(F.data == 'modules_slots')
async def on_modules_slots(callback: CallbackQuery):
    """Меню слотов"""
    user_id = callback.from_user.id
    
    # Получаем установленные модули
    installed = await db.get_installed_modules_by_slots(user_id)
    
    # Формируем текст
    text = '📦 <b>Слоты модулей</b>\n'
    
    keyboard_buttons = []
    
    for slot_num in range(1, MAX_SLOTS + 1):
        module = installed.get(slot_num)
        
        if module:
            rarity = Rarity(module.get('rarity', 1))
            name = module.get('name', '??-??')
            button_text = f"{RARITY_EMOJI[rarity]} {name}"
            action = f'module_uninstall_confirm:{module["module_id"]}'
        else:
            # Слот 4 — привилегированный
            if slot_num == 4:
                # TODO: проверка привилегии
                button_text = "💎🔒"
                action = 'modules_slot_premium'
            else:
                button_text = "Пусто"
                action = f'modules_slot_empty:{slot_num}'
        
        keyboard_buttons.append([
            InlineKeyboardButton(text=button_text, callback_data=action)
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text='⬅️ Назад', callback_data='modules_back'),
        InlineKeyboardButton(text='❌ Закрыть', callback_data='modules_close')
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
    await callback.answer()


@router.callback_query(F.data.startswith('modules_slot_empty:'))
async def on_slot_empty(callback: CallbackQuery):
    """Пустой слот"""
    slot_num = int(callback.data.split(':')[1])
    await callback.answer(f'Слот {slot_num} пуст. Выберите модуль для установки.', show_alert=True)


@router.callback_query(F.data == 'modules_slot_premium')
async def on_slot_premium(callback: CallbackQuery):
    """Привилегированный слот"""
    await callback.answer('💎 Этот слот доступен только с привилегией', show_alert=True)


# ==================== УСТАНОВКА МОДУЛЯ ====================

@router.callback_query(F.data.startswith('module_select_slot:'))
async def on_module_select_slot(callback: CallbackQuery):
    """Выбор слота для установки"""
    module_id = int(callback.data.split(':')[1])
    user_id = callback.from_user.id
    
    module = await db.get_module_by_id(user_id, module_id)
    if not module:
        await callback.answer('Модуль не найден', show_alert=True)
        return
    
    # Получаем установленные модули
    installed = await db.get_installed_modules_by_slots(user_id)
    
    text = f'📦 <b>Выбери слот для установки</b>\n{module["name"]} #{module_id}'
    
    keyboard_buttons = []
    
    for slot_num in range(1, MAX_SLOTS + 1):
        if slot_num in installed:
            # Слот занят
            mod = installed[slot_num]
            button_text = f"Слот {slot_num} ({RARITY_EMOJI[Rarity(mod['rarity'])]} {mod['name']})"
            action = f'modules_slot_occupied:{slot_num}'
        elif slot_num == 4:
            # Привилегированный слот
            button_text = f"Слот {slot_num} (💎🔒)"
            action = f'module_install:{module_id}:{slot_num}:premium'
        else:
            button_text = f"Слот {slot_num} (пусто)"
            action = f'module_install:{module_id}:{slot_num}'
        
        keyboard_buttons.append([
            InlineKeyboardButton(text=button_text, callback_data=action)
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text='⬅️ Отмена', callback_data=f'module_view:{module_id}')
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
    await callback.answer()


@router.callback_query(F.data.startswith('modules_slot_occupied:'))
async def on_slot_occupied(callback: CallbackQuery):
    """Слот занят"""
    slot_num = int(callback.data.split(':')[1])
    await callback.answer(f'Слот {slot_num} уже занят', show_alert=True)


@router.callback_query(F.data.startswith('module_install:'))
async def on_module_install(callback: CallbackQuery):
    """Установка модуля в слот"""
    parts = callback.data.split(':')
    module_id = int(parts[1])
    slot_num = int(parts[2])
    user_id = callback.from_user.id
    
    # Проверка привилегии для слота 4
    if slot_num == 4 and len(parts) < 4:
        await callback.answer('💎 Этот слот требует привилегию', show_alert=True)
        return
    
    # Устанавливаем
    success = await db.install_module_to_slot(user_id, module_id, slot_num)
    
    if success:
        await callback.answer(f'✅ Модуль установлен в слот {slot_num}!')
    else:
        await callback.answer('❌ Ошибка установки', show_alert=True)
    
    # Возвращаемся к карточке
    await on_module_view(callback)


# ==================== СНЯТИЕ МОДУЛЯ ====================

@router.callback_query(F.data.startswith('module_uninstall_confirm:'))
async def on_module_uninstall_confirm(callback: CallbackQuery):
    """Подтверждение снятия модуля"""
    module_id = int(callback.data.split(':')[1])
    user_id = callback.from_user.id
    
    module = await db.get_module_by_id(user_id, module_id)
    if not module:
        await callback.answer('Модуль не найден', show_alert=True)
        return
    
    slot = module.get('slot')
    name = module.get('name', '??-??')
    
    text = f'📦 <b>Снять модуль {name} #{module_id} со слота {slot}?</b>'
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='✅ Снять', callback_data=f'module_uninstall:{module_id}'),
            InlineKeyboardButton(text='⬅️ Отмена', callback_data=f'module_view:{module_id}')
        ]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
    await callback.answer()


@router.callback_query(F.data.startswith('module_uninstall:'))
async def on_module_uninstall(callback: CallbackQuery):
    """Снятие модуля"""
    module_id = int(callback.data.split(':')[1])
    user_id = callback.from_user.id
    
    success = await db.uninstall_module_from_slot(user_id, module_id)
    
    if success:
        await callback.answer('✅ Модуль снят!')
    else:
        await callback.answer('❌ Ошибка', show_alert=True)
    
    await show_modules_inventory(callback.message, user_id, page=1, edit=True)


# ==================== УЛУЧШЕНИЕ МОДУЛЯ ====================

@router.callback_query(F.data.startswith('module_upgrade:'))
async def on_module_upgrade(callback: CallbackQuery):
    """Меню улучшения модуля"""
    module_id = int(callback.data.split(':')[1])
    user_id = callback.from_user.id
    
    module = await db.get_module_by_id(user_id, module_id)
    if not module:
        await callback.answer('Модуль не найден', show_alert=True)
        return
    
    rarity = Rarity(module.get('rarity', 1))
    
    if rarity >= Rarity.LEGENDARY:
        await callback.answer('Модуль нельзя улучшить — он уже легендарный', show_alert=True)
        return
    
    if module.get('slot') is not None:
        await callback.answer('Модуль надет. Сними его перед улучшением', show_alert=True)
        return
    
    # Получаем стоимость улучшения
    cost = ModuleSystem.get_upgrade_cost(rarity)
    if not cost:
        await callback.answer('Ошибка определения стоимости', show_alert=True)
        return
    
    # Получаем материалы пользователя
    inventory = await db.get_user_inventory(user_id)
    inventory_dict = {item['item_key']: item.get('quantity', 0) for item in inventory}
    
    # Формируем текст
    next_rarity = Rarity(rarity + 1)
    
    text = f'⭐️ <b>Улучшение модуля</b>\n\n'
    text += f'{module["name"]} #{module_id}\n\n'
    text += f'После улучшения:\n'
    text += f'Редкость: {RARITY_EMOJI[next_rarity]} {RARITY_NAME[next_rarity]}\n\n'
    
    # Показываем изменения бафов
    buffs = module.get('buffs', {})
    if isinstance(buffs, str):
        buffs = json.loads(buffs)
    
    text += '💚 Бафы:\n'
    for key, current_value in buffs.items():
        new_value = BUFF_VALUES[key][next_rarity]
        text += f'• {BUFF_NAMES[key]}: {current_value}% ➜ {new_value}%\n'
    
    # Показываем изменения дебафов
    debuffs = module.get('debuffs', {})
    if isinstance(debuffs, str):
        debuffs = json.loads(debuffs)
    
    text += '\n❤️ Дебафы:\n'
    for key, current_value in debuffs.items():
        new_value = DEBUFF_VALUES[key][next_rarity]
        text += f'• {DEBUFF_NAMES[key]}: {current_value}% ➜ {new_value}%\n'
    
    # Стоимость
    text += '\n<b>Стоимость:</b>\n'
    
    material_emojis = {
        'asteroid_rock': '🪨',
        'cosmic_silicon': '🔩',
        'metal_fragments': '⚙️',
        'energy_condenser': '⚡',
        'quantum_fragment': '💫',
        'xenotissue': '🧬',
        'plasma_core': '☄️',
        'astral_crystal': '🔮',
        'gravity_node': '🌀',
    }
    
    material_names = {
        'asteroid_rock': 'Астероидная порода',
        'cosmic_silicon': 'Космический кремний',
        'metal_fragments': 'Металлические фрагменты',
        'energy_condenser': 'Энергетический конденсатор',
        'quantum_fragment': 'Квантовый фрагмент',
        'xenotissue': 'Ксеноткань',
        'plasma_core': 'Плазменное ядро',
        'astral_crystal': 'Астральный кристалл',
        'gravity_node': 'Гравитационный узел',
    }
    
    can_upgrade = True
    for material_key, required in cost.items():
        have = inventory_dict.get(material_key, 0)
        emoji = material_emojis.get(material_key, '📦')
        name = material_names.get(material_key, material_key)
        
        if have < required:
            can_upgrade = False
            text += f'• {have}/{required} {emoji} {name} ❌\n'
        else:
            text += f'• {have}/{required} {emoji} {name}\n'
    
    keyboard_buttons = []
    
    if can_upgrade:
        keyboard_buttons.append([
            InlineKeyboardButton(text='⭐️ Улучшить', callback_data=f'module_upgrade_confirm:{module_id}')
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text='⬅️ Назад', callback_data=f'module_view:{module_id}')
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
    await callback.answer()


@router.callback_query(F.data.startswith('module_upgrade_confirm:'))
async def on_module_upgrade_confirm(callback: CallbackQuery):
    """Подтверждение улучшения"""
    module_id = int(callback.data.split(':')[1])
    user_id = callback.from_user.id
    
    module = await db.get_module_by_id(user_id, module_id)
    if not module:
        await callback.answer('Модуль не найден', show_alert=True)
        return
    
    rarity = Rarity(module.get('rarity', 1))
    cost = ModuleSystem.get_upgrade_cost(rarity)
    
    # Списываем материалы
    for material_key, amount in cost.items():
        await db.remove_item(user_id, material_key, amount)
    
    # Обновляем модуль
    buffs = module.get('buffs', {})
    if isinstance(buffs, str):
        buffs = json.loads(buffs)
    
    debuffs = module.get('debuffs', {})
    if isinstance(debuffs, str):
        debuffs = json.loads(debuffs)
    
    new_data = ModuleSystem.upgrade_module(buffs, debuffs, rarity)
    
    await db.update_module(user_id, module_id, new_data)
    
    await callback.answer('✅ Модуль успешно улучшен!', show_alert=True)
    
    # Показываем обновлённую карточку
    await on_module_view(callback)


# ==================== ПРОДАЖА МОДУЛЯ ====================

@router.callback_query(F.data.startswith('module_sell_confirm:'))
async def on_module_sell_confirm(callback: CallbackQuery):
    """Подтверждение продажи"""
    module_id = int(callback.data.split(':')[1])
    user_id = callback.from_user.id
    
    module = await db.get_module_by_id(user_id, module_id)
    if not module:
        await callback.answer('Модуль не найден', show_alert=True)
        return
    
    rarity = Rarity(module.get('rarity', 1))
    price = ModuleSystem.get_sell_price(rarity)
    name = module.get('name', '??-??')
    
    text = f'💰 <b>Продажа модуля</b>\n\n{name} #{module_id}\n\nСтоимость: {format_number(price)} ⚙️'
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='✅ Продать', callback_data=f'module_sell:{module_id}'),
            InlineKeyboardButton(text='⬅️ Отмена', callback_data=f'module_view:{module_id}')
        ]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
    await callback.answer()


@router.callback_query(F.data.startswith('module_sell:'))
async def on_module_sell(callback: CallbackQuery):
    """Продажа модуля"""
    module_id = int(callback.data.split(':')[1])
    user_id = callback.from_user.id
    
    module = await db.get_module_by_id(user_id, module_id)
    if not module:
        await callback.answer('Модуль не найден', show_alert=True)
        return
    
    rarity = Rarity(module.get('rarity', 1))
    price = ModuleSystem.get_sell_price(rarity)
    
    # Удаляем модуль
    await db.delete_module(user_id, module_id)
    
    # Добавляем металл
    await db.update_user_resources(user_id, metal=price)
    
    await callback.answer(f'✅ Модуль продан! Получено: {format_number(price)} ⚙️', show_alert=True)
    
    await show_modules_inventory(callback.message, user_id, page=1, edit=True)


# ==================== РАЗБОРКА МОДУЛЯ ====================

@router.callback_query(F.data.startswith('module_scrap_confirm:'))
async def on_module_scrap_confirm(callback: CallbackQuery):
    """Подтверждение разборки"""
    module_id = int(callback.data.split(':')[1])
    user_id = callback.from_user.id
    
    module = await db.get_module_by_id(user_id, module_id)
    if not module:
        await callback.answer('Модуль не найден', show_alert=True)
        return
    
    rarity = Rarity(module.get('rarity', 1))
    rewards = ModuleSystem.get_scrap_rewards(rarity)
    name = module.get('name', '??-??')
    
    material_emojis = {
        'asteroid_rock': '🪨',
        'cosmic_silicon': '🔩',
        'metal_fragments': '⚙️',
        'energy_condenser': '⚡',
        'quantum_fragment': '💫',
        'xenotissue': '🧬',
        'plasma_core': '☄️',
        'astral_crystal': '🔮',
        'gravity_node': '🌀',
    }
    
    material_names = {
        'asteroid_rock': 'Астероидная порода',
        'cosmic_silicon': 'Космический кремний',
        'metal_fragments': 'Металлические фрагменты',
        'energy_condenser': 'Энергетический конденсатор',
        'quantum_fragment': 'Квантовый фрагмент',
        'xenotissue': 'Ксеноткань',
        'plasma_core': 'Плазменное ядро',
        'astral_crystal': 'Астральный кристалл',
        'gravity_node': 'Гравитационный узел',
    }
    
    text = f'🗑️ <b>Разборка модуля</b>\n\n{name} #{module_id}\n\n<b>Вы получите:</b>\n'
    
    for key, value in rewards.items():
        if key == 'chance':
            continue
        emoji = material_emojis.get(key, '📦')
        name_mat = material_names.get(key, key)
        text += f'• {emoji} {name_mat} ×{value}\n'
    
    # Шансовые материалы
    if 'chance' in rewards:
        for key, (chance, amount) in rewards['chance'].items():
            emoji = material_emojis.get(key, '📦')
            name_mat = material_names.get(key, key)
            text += f'• {emoji} {name_mat} ×{amount} (шанс {chance}%)\n'
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='✅ Разобрать', callback_data=f'module_scrap:{module_id}'),
            InlineKeyboardButton(text='⬅️ Отмена', callback_data=f'module_view:{module_id}')
        ]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
    await callback.answer()


@router.callback_query(F.data.startswith('module_scrap:'))
async def on_module_scrap(callback: CallbackQuery):
    """Разборка модуля"""
    module_id = int(callback.data.split(':')[1])
    user_id = callback.from_user.id
    
    module = await db.get_module_by_id(user_id, module_id)
    if not module:
        await callback.answer('Модуль не найден', show_alert=True)
        return
    
    rarity = Rarity(module.get('rarity', 1))
    rewards = ModuleSystem.get_scrap_rewards(rarity)
    
    # Выдаём материалы
    for key, value in rewards.items():
        if key == 'chance':
            continue
        await db.add_item(user_id, key, value)
    
    # Шансовые материалы
    if 'chance' in rewards:
        for key, (chance, amount) in rewards['chance'].items():
            if random.randint(1, 100) <= chance:
                await db.add_item(user_id, key, amount)
    
    # Удаляем модуль
    await db.delete_module(user_id, module_id)
    
    await callback.answer('✅ Модуль разобран!', show_alert=True)
    
    await show_modules_inventory(callback.message, user_id, page=1, edit=True)
