"""
Админ-панель Telegram-бота (inline интерфейс)
Согласно Admin_panel.txt - полная реализация
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import aiosqlite
import random
import json
import os
import shutil

from database import db
from admin.keyboards import *
from admin.settings import AdminSettingsManager, RARITY_PRESETS
from game.modules import ModuleSystem, Rarity, RARITY_EMOJI, RARITY_NAME, BUFF_NAMES, DEBUFF_NAMES
from game.materials import MaterialSystem
from game.containers import ContainerSystem, ContainerType

router = Router()

# Инициализация менеджера настроек
settings_manager = AdminSettingsManager(db.db_path)


# ===== СОСТОЯНИЯ FSM =====

class AdminStates(StatesGroup):
    """Состояния админ-панели"""
    # Поиск игрока
    search_player = State()
    
    # Изменение ресурсов
    edit_resource_value = State()
    
    # Выдача
    give_container_amount = State()
    give_material_amount = State()
    give_module_confirm = State()
    
    # Бан
    ban_reason = State()
    ban_custom_duration = State()
    
    # Массовые операции
    mass_container_amount = State()
    mass_resources_amount = State()
    
    # Настройки
    edit_setting_value = State()
    
    # Создание ивента
    event_name = State()
    event_duration = State()


# ===== РОЛИ АДМИНОВ =====

ROLE_EMOJI = {
    "owner": "👑",
    "senior": "👾",
    "moderator": "🟢",
    "support": "🔹"
}

ROLE_NAMES = {
    "owner": "Владелец",
    "senior": "Старший администратор",
    "moderator": "Модератор",
    "support": "Саппорт"
}

# Права по ролям
ROLE_PERMISSIONS = {
    "owner": ["all"],
    "senior": ["players", "containers", "modules", "drop", "economy", "materials", "stats", "logs", "testing", "events", "backups", "metrics"],
    "moderator": ["players", "containers", "modules", "materials", "stats", "logs"],
    "support": ["stats", "logs"]
}


# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

async def get_admin_role(user_id: int) -> str:
    """Получить роль админа"""
    async with aiosqlite.connect(db.db_path) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute(
            "SELECT role FROM admins WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row["role"] if row else "support"


async def is_admin(user_id: int) -> bool:
    """Проверка прав админа"""
    async with aiosqlite.connect(db.db_path) as conn:
        async with conn.execute(
            "SELECT 1 FROM admins WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            result = await cursor.fetchone()
            print(f"[is_admin] Checking user {user_id}, result={result}")
            return result is not None


async def check_permission(user_id: int, permission: str) -> bool:
    """Проверка права доступа"""
    role = await get_admin_role(user_id)
    
    if role == "owner":
        return True
    
    permissions = ROLE_PERMISSIONS.get(role, [])
    return permission in permissions or "all" in permissions


async def log_action(admin_id: int, action: str, target_user_id: int = None, details: str = None):
    """Логирование действия админа"""
    async with aiosqlite.connect(db.db_path) as conn:
        await conn.execute(
            "INSERT INTO admin_logs (admin_id, action, target_user_id, details) VALUES (?, ?, ?, ?)",
            (admin_id, action, target_user_id, details)
        )
        await conn.commit()


def format_number(n: int) -> str:
    """Форматирование числа с разделителями"""
    return f"{n:,}".replace(",", " ")


def get_timestamp() -> str:
    """Получить текущее время"""
    return datetime.now().strftime("%d.%m.%Y %H:%M")


# ===== ГЛАВНОЕ МЕНЮ =====

@router.message(Command('admin'))
async def cmd_admin(message: Message):
    """Команда /admin - вход в админ-панель"""
    user_id = message.from_user.id
    
    # Проверка доступа
    admin_check = await is_admin(user_id)
    
    # Логирование для диагностики
    print(f"[ADMIN] User {user_id} tried /admin, is_admin={admin_check}")
    
    if not admin_check:
        # Для не-админов - тихий игнор или сообщение
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return
    
    role = await get_admin_role(user_id)
    role_name = ROLE_NAMES.get(role, "Саппорт")
    role_emoji = ROLE_EMOJI.get(role, "🔹")
    
    text = (
        f"🛠 <b>ПАНЕЛЬ АДМИНИСТРАТОРА</b>\n\n"
        f"{role_emoji} Роль: {role_name}\n"
        f"🕐 {get_timestamp()}\n\n"
        f"Выбери раздел для управления:"
    )
    
    await message.answer(
        text,
        reply_markup=get_admin_main_keyboard(role),
        parse_mode='HTML'
    )


@router.callback_query(F.data == "admin:main")
async def admin_main(callback: CallbackQuery):
    """Возврат в главное меню"""
    user_id = callback.from_user.id
    
    if not await is_admin(user_id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    role = await get_admin_role(user_id)
    role_name = ROLE_NAMES.get(role, "Саппорт")
    role_emoji = ROLE_EMOJI.get(role, "🔹")
    
    text = (
        f"🛠 <b>ПАНЕЛЬ АДМИНИСТРАТОРА</b>\n\n"
        f"{role_emoji} Роль: {role_name}\n"
        f"🕐 {get_timestamp()}\n\n"
        f"Выбери раздел для управления:"
    )
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_main_keyboard(role),
            parse_mode='HTML'
        )
    except:
        pass
    
    await callback.answer()


@router.callback_query(F.data == "admin:close")
async def admin_close(callback: CallbackQuery):
    """Закрытие админ-панели"""
    try:
        await callback.message.delete()
    except:
        pass
    await callback.answer()


# ===== РАЗДЕЛ ИГРОКИ =====

@router.callback_query(F.data == "admin:players")
async def admin_players_menu(callback: CallbackQuery):
    """Меню управления игроками"""
    user_id = callback.from_user.id
    
    if not await check_permission(user_id, "players"):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    text = (
        "👤 <b>УПРАВЛЕНИЕ ИГРОКАМИ</b>\n\n"
        "Выбери действие:"
    )
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_players_menu_keyboard(),
            parse_mode='HTML'
        )
    except:
        pass
    
    await callback.answer()


@router.callback_query(F.data == "admin:players:find")
async def admin_players_find(callback: CallbackQuery, state: FSMContext):
    """Поиск игрока"""
    await state.set_state(AdminStates.search_player)
    
    text = (
        "🔍 <b>ПОИСК ИГРОКА</b>\n\n"
        "Введите ID или username игрока.\n"
        "Минимум 3 символа для поиска."
    )
    
    try:
        await callback.message.edit_text(text, parse_mode='HTML')
    except:
        pass
    
    await callback.answer()


@router.message(AdminStates.search_player)
async def admin_players_search_process(message: Message, state: FSMContext):
    """Обработка поиска игрока"""
    if not await is_admin(message.from_user.id):
        await state.clear()
        return
    
    query = message.text.strip()
    
    if len(query) < 3:
        await message.answer("❌ Минимум 3 символа для поиска!")
        return
    
    # Поиск в БД
    async with aiosqlite.connect(db.db_path) as conn:
        conn.row_factory = aiosqlite.Row
        
        # Пробуем как ID
        try:
            user_id = int(query)
            async with conn.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    await state.clear()
                    await show_player_card(message, dict(row))
                    return
        except ValueError:
            pass
        
        # Поиск по username
        async with conn.execute(
            "SELECT * FROM users WHERE username LIKE ? OR first_name LIKE ? LIMIT 10",
            (f"%{query}%", f"%{query}%")
        ) as cursor:
            rows = await cursor.fetchall()
        
        if not rows:
            await message.answer("❌ Игрок не найден!")
            return
        
        if len(rows) == 1:
            await state.clear()
            await show_player_card(message, dict(rows[0]))
            return
        
        # Несколько результатов
        text = "🔍 <b>РЕЗУЛЬТАТЫ ПОИСКА:</b>\n\n"
        builder = []
        
        for row in rows[:10]:
            user = dict(row)
            username = user.get('username') or user.get('first_name') or str(user['user_id'])
            builder.append([
                {"text": f"@{username} ({user['user_id']})", "callback_data": f"admin:players:card:{user['user_id']}"}
            ])
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=btn[0]["text"], callback_data=btn[0]["callback_data"])] 
            for btn in builder
        ])
        
        await message.answer(text, reply_markup=keyboard, parse_mode='HTML')
        await state.clear()


@router.callback_query(F.data.startswith("admin:players:card:"))
async def admin_player_card(callback: CallbackQuery):
    """Показать карточку игрока"""
    user_id = int(callback.data.split(":")[-1])
    
    async with aiosqlite.connect(db.db_path) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
        
        if not row:
            await callback.answer("❌ Игрок не найден", show_alert=True)
            return
        
        user = dict(row)
    
    await show_player_card(callback.message, user, edit=True)
    await callback.answer()


async def show_player_card(message_or_callback, user: dict, edit: bool = False):
    """Показать карточку игрока"""
    user_id = user['user_id']
    username = user.get('username') or user.get('first_name') or 'Неизвестно'
    
    # Получаем статистику
    async with aiosqlite.connect(db.db_path) as conn:
        conn.row_factory = aiosqlite.Row
        
        # Контейнеры
        async with conn.execute(
            "SELECT COUNT(*) as count FROM inventory WHERE user_id = ? AND item_key LIKE 'container_%'",
            (user_id,)
        ) as cursor:
            containers_row = await cursor.fetchone()
            containers_count = containers_row['count'] if containers_row else 0
        
        # Модули
        async with conn.execute(
            "SELECT COUNT(*) as count FROM modules WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            modules_row = await cursor.fetchone()
            modules_count = modules_row['count'] if modules_row else 0
        
        # Материалы
        async with conn.execute(
            "SELECT SUM(quantity) as total FROM inventory WHERE user_id = ? AND item_key IN (SELECT item_key FROM items WHERE item_type = 'material')",
            (user_id,)
        ) as cursor:
            materials_row = await cursor.fetchone()
            materials_count = materials_row['total'] if materials_row and materials_row['total'] else 0
    
    text = (
        f"👤 <b>КАРТОЧКА ИГРОКА</b>\n\n"
        f"🆔 ID: {user_id}\n"
        f"📝 Username: @{username}\n"
        f"📅 Регистрация: {user.get('created_at', 'N/A')[:10] if user.get('created_at') else 'N/A'}\n\n"
        f"💰 <b>РЕСУРСЫ:</b>\n"
        f"⚙️ Металл: {format_number(user.get('metal', 0))}\n"
        f"💎 Кристаллы: {format_number(user.get('crystals', 0))}\n"
        f"🕳️ Тёмная материя: {format_number(user.get('dark_matter', 0))}\n\n"
        f"📦 <b>ИНВЕНТАРЬ:</b>\n"
        f"📦 Контейнеры: {containers_count}\n"
        f"🧩 Модули: {modules_count}\n"
        f"🧱 Материалы: {materials_count}"
    )
    
    keyboard = get_player_card_keyboard(user_id)
    
    if edit:
        try:
            await message_or_callback.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
        except:
            await message_or_callback.answer(text, reply_markup=keyboard, parse_mode='HTML')
    else:
        await message_or_callback.answer(text, reply_markup=keyboard, parse_mode='HTML')


# ===== ИЗМЕНЕНИЕ РЕСУРСОВ =====

@router.callback_query(F.data.startswith("admin:players:resources"))
async def admin_players_resources(callback: CallbackQuery):
    """Выбор ресурса для изменения"""
    parts = callback.data.split(":")
    
    if len(parts) > 3:
        user_id = int(parts[3])
    else:
        # Нужно получить ID игрока из контекста
        await callback.answer("❌ Сначала найдите игрока", show_alert=True)
        return
    
    user = await db.get_user(user_id)
    if not user:
        await callback.answer("❌ Игрок не найден", show_alert=True)
        return
    
    text = (
        f"💰 <b>ИЗМЕНЕНИЕ РЕСУРСОВ</b>\n\n"
        f"Текущие ресурсы игрока @{user.get('username', user_id)}:\n\n"
        f"⚙️ Металл: {format_number(user.get('metal', 0))}\n"
        f"💎 Кристаллы: {format_number(user.get('crystals', 0))}\n"
        f"🕳️ Тёмная материя: {format_number(user.get('dark_matter', 0))}\n\n"
        f"Выбери ресурс для изменения:"
    )
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_resource_select_keyboard(user_id),
            parse_mode='HTML'
        )
    except:
        pass
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin:players:res:"))
async def admin_players_res_select(callback: CallbackQuery, state: FSMContext):
    """Выбор ресурса - запрос значения"""
    parts = callback.data.split(":")
    user_id = int(parts[3])
    resource = parts[4]
    
    user = await db.get_user(user_id)
    current_value = user.get(resource, 0) if user else 0
    
    await state.update_data(user_id=user_id, resource=resource, current_value=current_value)
    await state.set_state(AdminStates.edit_resource_value)
    
    resource_names = {
        "metal": "⚙️ Металл",
        "crystals": "💎 Кристаллы",
        "dark_matter": "🕳️ Тёмная материя"
    }
    
    text = (
        f"💰 <b>ИЗМЕНЕНИЕ РЕСУРСА</b>\n\n"
        f"Ресурс: {resource_names.get(resource, resource)}\n"
        f"Текущее: {format_number(current_value)}\n\n"
        f"Введите новое значение:"
    )
    
    try:
        await callback.message.edit_text(text, parse_mode='HTML')
    except:
        pass
    
    await callback.answer()


@router.message(AdminStates.edit_resource_value)
async def admin_players_res_value(message: Message, state: FSMContext):
    """Ввод нового значения ресурса"""
    if not await is_admin(message.from_user.id):
        await state.clear()
        return
    
    data = await state.get_data()
    user_id = data['user_id']
    resource = data['resource']
    current_value = data['current_value']
    
    try:
        new_value = int(message.text.replace(" ", "").replace(",", ""))
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    await state.clear()
    
    resource_names = {
        "metal": "⚙️ Металл",
        "crystals": "💎 Кристаллы",
        "dark_matter": "🕳️ Тёмная материя"
    }
    
    text = (
        f"✅ <b>ПОДТВЕРЖДЕНИЕ</b>\n\n"
        f"Изменить {resource_names.get(resource, resource)}:\n"
        f"{format_number(current_value)} → {format_number(new_value)}\n\n"
        f"Игрок ID: {user_id}"
    )
    
    builder = [
        [
            {"text": "✅ Подтвердить", "callback_data": f"admin:confirm:res:{user_id}:{resource}:{new_value}"},
            {"text": "⬅️ Отмена", "callback_data": f"admin:players:card:{user_id}"}
        ]
    ]
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn[0]["text"], callback_data=btn[0]["callback_data"]),
         InlineKeyboardButton(text=btn[1]["text"], callback_data=btn[1]["callback_data"])]
        for btn in builder
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode='HTML')


@router.callback_query(F.data.startswith("admin:confirm:res:"))
async def admin_confirm_res(callback: CallbackQuery):
    """Подтверждение изменения ресурса"""
    parts = callback.data.split(":")
    user_id = int(parts[3])
    resource = parts[4]
    new_value = int(parts[5])
    
    # Получаем текущее значение
    user = await db.get_user(user_id)
    old_value = user.get(resource, 0) if user else 0
    
    # Вычисляем разницу
    diff = new_value - old_value
    
    # Обновляем
    await db.update_user_resources(user_id, **{resource: diff})
    
    # Логируем
    await log_action(
        admin_id=callback.from_user.id,
        action="edit_resource",
        target_user_id=user_id,
        details=f"{resource}: {old_value} -> {new_value}"
    )
    
    await callback.answer(f"✅ Ресурс изменён: {format_number(new_value)}", show_alert=True)
    
    # Возвращаемся к карточке
    user = await db.get_user(user_id)
    await show_player_card(callback.message, user, edit=True)


# ===== ВЫДАЧА КОНТЕЙНЕРОВ =====

@router.callback_query(F.data.startswith("admin:players:give_container"))
async def admin_give_container(callback: CallbackQuery):
    """Выбор типа контейнера для выдачи"""
    parts = callback.data.split(":")
    user_id = int(parts[3]) if len(parts) > 3 else None
    
    text = (
        "📦 <b>ВЫДАЧА КОНТЕЙНЕРОВ</b>\n\n"
        "Выбери тип контейнера:"
    )
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_container_type_keyboard("give_container", user_id),
            parse_mode='HTML'
        )
    except:
        pass
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin:players:give_container:container:"))
async def admin_give_container_type(callback: CallbackQuery, state: FSMContext):
    """Выбор количества контейнеров"""
    parts = callback.data.split(":")
    user_id = int(parts[3])
    container_type = parts[5]
    
    await state.update_data(user_id=user_id, container_type=container_type)
    await state.set_state(AdminStates.give_container_amount)
    
    container_names = {
        "common": "📦 Обычный",
        "rare": "🎁 Редкий",
        "epic": "💎 Эпический",
        "mythic": "👑 Мифический",
        "legendary": "🔥 Легендарный",
        "ksm": "🧰 КСМ"
    }
    
    text = (
        f"📦 <b>ВЫДАЧА КОНТЕЙНЕРОВ</b>\n\n"
        f"Тип: {container_names.get(container_type, container_type)}\n\n"
        f"Введите количество (макс. 100):"
    )
    
    try:
        await callback.message.edit_text(text, parse_mode='HTML')
    except:
        pass
    
    await callback.answer()


@router.message(AdminStates.give_container_amount)
async def admin_give_container_amount(message: Message, state: FSMContext):
    """Подтверждение выдачи контейнеров"""
    if not await is_admin(message.from_user.id):
        await state.clear()
        return
    
    data = await state.get_data()
    user_id = data['user_id']
    container_type = data['container_type']
    
    try:
        amount = int(message.text)
        if amount < 1 or amount > 100:
            await message.answer("❌ Количество от 1 до 100!")
            return
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    await state.clear()
    
    container_names = {
        "common": "📦 Обычный",
        "rare": "🎁 Редкий",
        "epic": "💎 Эпический",
        "mythic": "👑 Мифический",
        "legendary": "🔥 Легендарный",
        "ksm": "🧰 КСМ"
    }
    
    text = (
        f"✅ <b>ПОДТВЕРЖДЕНИЕ</b>\n\n"
        f"Выдать {amount} {container_names.get(container_type, container_type)} контейнер(ов)?\n\n"
        f"Игрок ID: {user_id}"
    )
    
    builder = [
        [
            {"text": "✅ Подтвердить", "callback_data": f"admin:confirm:container:{user_id}:{container_type}:{amount}"},
            {"text": "⬅️ Отмена", "callback_data": f"admin:players:card:{user_id}"}
        ]
    ]
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn[0]["text"], callback_data=btn[0]["callback_data"]),
         InlineKeyboardButton(text=btn[1]["text"], callback_data=btn[1]["callback_data"])]
        for btn in builder
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode='HTML')


@router.callback_query(F.data.startswith("admin:confirm:container:"))
async def admin_confirm_container(callback: CallbackQuery):
    """Подтверждение выдачи контейнера"""
    parts = callback.data.split(":")
    user_id = int(parts[3])
    container_type = parts[4]
    amount = int(parts[5])
    
    # Выдаём контейнеры
    container_item_key = f"container_{container_type}"
    
    for _ in range(amount):
        await db.add_item(user_id, container_item_key, 1)
    
    # Логируем
    await log_action(
        admin_id=callback.from_user.id,
        action="give_container",
        target_user_id=user_id,
        details=f"{container_type} x{amount}"
    )
    
    container_names = {
        "common": "📦 Обычный",
        "rare": "🎁 Редкий",
        "epic": "💎 Эпический",
        "mythic": "👑 Мифический",
        "legendary": "🔥 Легендарный",
        "ksm": "🧰 КСМ"
    }
    
    await callback.answer(
        f"✅ Выдано {amount} {container_names.get(container_type, container_type)}",
        show_alert=True
    )
    
    # Возвращаемся к карточке
    user = await db.get_user(user_id)
    await show_player_card(callback.message, user, edit=True)


# ===== ВЫДАЧА МОДУЛЕЙ =====

@router.callback_query(F.data.startswith("admin:players:give_module"))
async def admin_give_module(callback: CallbackQuery):
    """Выбор редкости модуля"""
    parts = callback.data.split(":")
    user_id = int(parts[3]) if len(parts) > 3 else None
    
    text = (
        "🧩 <b>ВЫДАЧА МОДУЛЯ</b>\n\n"
        "Выбери редкость модуля:"
    )
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_module_rarity_keyboard("give_module", user_id),
            parse_mode='HTML'
        )
    except:
        pass
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin:players:give_module:module:"))
async def admin_give_module_rarity(callback: CallbackQuery):
    """Генерация и предпросмотр модуля"""
    parts = callback.data.split(":")
    user_id = int(parts[3])
    rarity_name = parts[5]
    
    # Маппинг названий
    rarity_map = {
        "common": Rarity.COMMON,
        "rare": Rarity.RARE,
        "epic": Rarity.EPIC,
        "mythic": Rarity.MYTHIC,
        "legendary": Rarity.LEGENDARY
    }
    
    rarity = rarity_map.get(rarity_name, Rarity.COMMON)
    
    # Генерируем модуль
    from game.modules import BUFF_KEYS, DEBUFF_KEYS, BUFF_COUNT, DEBUFF_COUNT, BUFF_VALUES, DEBUFF_VALUES
    
    name = ModuleSystem.generate_name()
    buff_keys = ModuleSystem.select_effects(BUFF_KEYS, BUFF_COUNT[rarity])
    debuff_keys = ModuleSystem.select_effects(DEBUFF_KEYS, DEBUFF_COUNT[rarity])
    
    buffs = {key: BUFF_VALUES[key][rarity] for key in buff_keys}
    debuffs = {key: DEBUFF_VALUES[key][rarity] for key in debuff_keys}
    
    # Форматируем
    text = (
        f"🧩 <b>СГЕНЕРИРОВАН МОДУЛЬ</b>\n\n"
        f"{RARITY_EMOJI[rarity]} {name}\n\n"
        f"💚 <b>Бафы:</b>\n"
    )
    
    for key, value in buffs.items():
        name_buf = BUFF_NAMES.get(key, key)
        text += f"• {name_buf}: +{value}%\n"
    
    text += f"\n❤️ <b>Дебафы:</b>\n"
    for key, value in debuffs.items():
        name_buf = DEBUFF_NAMES.get(key, key)
        text += f"• {name_buf}: +{value}%\n"
    
    text += f"\nВыдать этот модуль игроку ID: {user_id}?"
    
    # Сохраняем данные модуля в callback (упрощённо - в cache)
    from core.cache import cache
    module_data = {
        "name": name,
        "rarity": int(rarity),
        "buffs": buffs,
        "debuffs": debuffs,
        "user_id": user_id
    }
    await cache.set(f"admin_module:{callback.from_user.id}", module_data, ttl=300)
    
    builder = [
        [
            {"text": "✅ Выдать", "callback_data": f"admin:confirm:module:{user_id}"},
            {"text": "🔄 Сгенерировать другой", "callback_data": f"admin:players:give_module:{user_id}:module:{rarity_name}"}
        ],
        [
            {"text": "⬅️ Отмена", "callback_data": f"admin:players:card:{user_id}"}
        ]
    ]
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn[0]["text"], callback_data=btn[0]["callback_data"]),
         InlineKeyboardButton(text=btn[1]["text"], callback_data=btn[1]["callback_data"])]
        for btn in builder[:-1]
    ] + [[InlineKeyboardButton(text=builder[-1][0]["text"], callback_data=builder[-1][0]["callback_data"])]])
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
    except:
        pass
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin:confirm:module:"))
async def admin_confirm_module(callback: CallbackQuery):
    """Подтверждение выдачи модуля"""
    user_id = int(callback.data.split(":")[3])
    
    from core.cache import cache
    module_data = await cache.get(f"admin_module:{callback.from_user.id}")
    
    if not module_data:
        await callback.answer("❌ Сессия истекла", show_alert=True)
        return
    
    # Сохраняем модуль в БД
    async with aiosqlite.connect(db.db_path) as conn:
        cursor = await conn.execute(
            """INSERT INTO modules (user_id, name, rarity, buffs, debuffs, slot, created_at)
               VALUES (?, ?, ?, ?, ?, NULL, CURRENT_TIMESTAMP)""",
            (
                module_data["user_id"],
                module_data["name"],
                module_data["rarity"],
                json.dumps(module_data["buffs"]),
                json.dumps(module_data["debuffs"])
            )
        )
        await conn.commit()
        module_id = cursor.lastrowid
    
    # Логируем
    await log_action(
        admin_id=callback.from_user.id,
        action="give_module",
        target_user_id=user_id,
        details=f"Module #{module_id}: {module_data['name']}"
    )
    
    await cache.delete(f"admin_module:{callback.from_user.id}")
    
    await callback.answer(f"✅ Модуль #{module_id} выдан", show_alert=True)
    
    # Возвращаемся к карточке
    user = await db.get_user(user_id)
    await show_player_card(callback.message, user, edit=True)


# ===== ВЫДАЧА МАТЕРИАЛОВ =====

@router.callback_query(F.data.startswith("admin:players:give_material"))
async def admin_give_material(callback: CallbackQuery):
    """Выбор материала для выдачи"""
    parts = callback.data.split(":")
    user_id = int(parts[3]) if len(parts) > 3 else None
    
    text = (
        "🧱 <b>ВЫДАЧА МАТЕРИАЛОВ</b>\n\n"
        "Выбери материал:"
    )
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_materials_keyboard(1, "give_material", user_id),
            parse_mode='HTML'
        )
    except:
        pass
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin:players:give_material:material:"))
async def admin_give_material_select(callback: CallbackQuery, state: FSMContext):
    """Выбор количества материала"""
    parts = callback.data.split(":")
    user_id = int(parts[3])
    material_key = parts[5]
    
    material = MaterialSystem.get_material(material_key)
    
    await state.update_data(user_id=user_id, material_key=material_key)
    await state.set_state(AdminStates.give_material_amount)
    
    text = (
        f"🧱 <b>ВЫДАЧА МАТЕРИАЛА</b>\n\n"
        f"Материал: {material.emoji if material else '📦'} {material.name if material else material_key}\n\n"
        f"Введите количество (макс. 1000):"
    )
    
    try:
        await callback.message.edit_text(text, parse_mode='HTML')
    except:
        pass
    
    await callback.answer()


@router.message(AdminStates.give_material_amount)
async def admin_give_material_amount(message: Message, state: FSMContext):
    """Подтверждение выдачи материала"""
    if not await is_admin(message.from_user.id):
        await state.clear()
        return
    
    data = await state.get_data()
    user_id = data['user_id']
    material_key = data['material_key']
    
    try:
        amount = int(message.text)
        if amount < 1 or amount > 1000:
            await message.answer("❌ Количество от 1 до 1000!")
            return
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    await state.clear()
    
    material = MaterialSystem.get_material(material_key)
    
    text = (
        f"✅ <b>ПОДТВЕРЖДЕНИЕ</b>\n\n"
        f"Выдать {amount} {material.emoji if material else '📦'} {material.name if material else material_key}?\n\n"
        f"Игрок ID: {user_id}"
    )
    
    builder = [
        [
            {"text": "✅ Подтвердить", "callback_data": f"admin:confirm:material:{user_id}:{material_key}:{amount}"},
            {"text": "⬅️ Отмена", "callback_data": f"admin:players:card:{user_id}"}
        ]
    ]
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn[0]["text"], callback_data=btn[0]["callback_data"]),
         InlineKeyboardButton(text=btn[1]["text"], callback_data=btn[1]["callback_data"])]
        for btn in builder
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode='HTML')


@router.callback_query(F.data.startswith("admin:confirm:material:"))
async def admin_confirm_material(callback: CallbackQuery):
    """Подтверждение выдачи материала"""
    parts = callback.data.split(":")
    user_id = int(parts[3])
    material_key = parts[4]
    amount = int(parts[5])
    
    # Выдаём материал
    await db.add_item(user_id, material_key, amount)
    
    material = MaterialSystem.get_material(material_key)
    
    # Логируем
    await log_action(
        admin_id=callback.from_user.id,
        action="give_material",
        target_user_id=user_id,
        details=f"{material_key} x{amount}"
    )
    
    await callback.answer(
        f"✅ Выдано {amount} {material.emoji if material else '📦'} {material.name if material else material_key}",
        show_alert=True
    )
    
    # Возвращаемся к карточке
    user = await db.get_user(user_id)
    await show_player_card(callback.message, user, edit=True)


# ===== БАН ИГРОКА =====

@router.callback_query(F.data.regexp(r"^admin:players:ban:\d+$"))
async def admin_ban_menu(callback: CallbackQuery):
    """Меню бана игрока"""
    user_id = int(callback.data.split(":")[3])
    
    user = await db.get_user(user_id)
    if not user:
        await callback.answer("❌ Игрок не найден", show_alert=True)
        return
    
    text = (
        f"🚫 <b>БАН ИГРОКА</b>\n\n"
        f"Игрок: @{user.get('username', user_id)}\n"
        f"🆔 ID: {user_id}\n\n"
        f"Выбери срок бана:"
    )
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_ban_duration_keyboard(user_id),
            parse_mode='HTML'
        )
    except:
        pass
    
    await callback.answer()


@router.callback_query(F.data.contains("admin:players:ban:") and (F.data.contains(":1h") or F.data.contains(":24h") or F.data.contains(":7d") or F.data.contains(":forever")))
async def admin_ban_execute(callback: CallbackQuery, state: FSMContext):
    """Выполнение бана"""
    parts = callback.data.split(":")
    user_id = int(parts[3])
    duration = parts[4]
    
    # Вычисляем время бана
    if duration == "forever":
        duration_hours = None
        expires_at = None
        duration_text = "Навсегда"
    elif duration == "1h":
        duration_hours = 1
        expires_at = datetime.now() + timedelta(hours=1)
        duration_text = "1 час"
    elif duration == "24h":
        duration_hours = 24
        expires_at = datetime.now() + timedelta(hours=24)
        duration_text = "24 часа"
    elif duration == "7d":
        duration_hours = 168
        expires_at = datetime.now() + timedelta(days=7)
        duration_text = "7 дней"
    else:
        await callback.answer("❌ Неверный срок", show_alert=True)
        return
    
    # Запрашиваем причину
    await state.update_data(user_id=user_id, duration_hours=duration_hours, expires_at=expires_at, duration_text=duration_text)
    await state.set_state(AdminStates.ban_reason)
    
    text = (
        f"🚫 <b>БАН ИГРОКА</b>\n\n"
        f"Срок: {duration_text}\n\n"
        f"Введите причину бана (или отправьте '-' чтобы пропустить):"
    )
    
    try:
        await callback.message.edit_text(text, parse_mode='HTML')
    except:
        pass
    
    await callback.answer()


@router.message(AdminStates.ban_reason)
async def admin_ban_reason(message: Message, state: FSMContext):
    """Причина бана и подтверждение"""
    if not await is_admin(message.from_user.id):
        await state.clear()
        return
    
    data = await state.get_data()
    user_id = data['user_id']
    duration_hours = data['duration_hours']
    expires_at = data['expires_at']
    duration_text = data['duration_text']
    
    reason = message.text if message.text != "-" else "Не указана"
    
    await state.clear()
    
    # Баним игрока
    async with aiosqlite.connect(db.db_path) as conn:
        # Обновляем статус в users
        await conn.execute(
            "UPDATE users SET is_banned = 1 WHERE user_id = ?",
            (user_id,)
        )
        
        # Добавляем запись в bans
        await conn.execute(
            """INSERT INTO bans (user_id, admin_id, reason, duration_hours, banned_at, expires_at, status)
               VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?, 'active')""",
            (user_id, message.from_user.id, reason, duration_hours, expires_at.isoformat() if expires_at else None)
        )
        
        await conn.commit()
    
    user = await db.get_user(user_id)
    
    # Логируем
    await log_action(
        admin_id=message.from_user.id,
        action="ban_player",
        target_user_id=user_id,
        details=f"Duration: {duration_text}, Reason: {reason}"
    )
    
    await message.answer(
        f"✅ Игрок @{user.get('username', user_id)} заблокирован на {duration_text}",
        parse_mode='HTML'
    )
    
    # Возвращаемся к карточке
    await show_player_card(message, user)


# ===== РАЗДЕЛ КОНТЕЙНЕРЫ =====

@router.callback_query(F.data == "admin:containers")
async def admin_containers_menu(callback: CallbackQuery):
    """Меню управления контейнерами"""
    if not await check_permission(callback.from_user.id, "containers"):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    text = (
        "📦 <b>УПРАВЛЕНИЕ КОНТЕЙНЕРАМИ</b>\n\n"
        "Настройки выпадения из контейнеров:"
    )
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_containers_menu_keyboard(),
            parse_mode='HTML'
        )
    except:
        pass
    
    await callback.answer()


@router.callback_query(F.data == "admin:containers:stats")
async def admin_containers_stats(callback: CallbackQuery):
    """Статистика контейнеров"""
    async with aiosqlite.connect(db.db_path) as conn:
        # Всего открыто
        async with conn.execute(
            "SELECT COUNT(*) FROM containers WHERE status = 'opened'"
        ) as cursor:
            total_opened = (await cursor.fetchone())[0]
        
        # По типам
        async with conn.execute(
            "SELECT container_type, COUNT(*) as count FROM containers WHERE status = 'opened' GROUP BY container_type",
        ) as cursor:
            by_type = await cursor.fetchall()
    
    text = (
        "📊 <b>СТАТИСТИКА КОНТЕЙНЕРОВ</b>\n\n"
        f"Всего открыто: {format_number(total_opened)}\n\n"
        "По типам:\n"
    )
    
    type_names = {
        "common": "📦 Обычных",
        "rare": "🎁 Редких",
        "epic": "💎 Эпических",
        "mythic": "👑 Мифических",
        "legendary": "🔥 Легендарных"
    }
    
    for container_type, count in by_type:
        text += f"{type_names.get(container_type, container_type)}: {format_number(count)}\n"
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard("admin:containers"),
            parse_mode='HTML'
        )
    except:
        pass
    
    await callback.answer()


# ===== РАЗДЕЛ МОДУЛИ =====

@router.callback_query(F.data == "admin:modules")
async def admin_modules_menu(callback: CallbackQuery):
    """Меню управления модулями"""
    if not await check_permission(callback.from_user.id, "modules"):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    text = (
        "🧩 <b>УПРАВЛЕНИЕ МОДУЛЯМИ</b>"
    )
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_modules_menu_keyboard(),
            parse_mode='HTML'
        )
    except:
        pass
    
    await callback.answer()


@router.callback_query(F.data == "admin:modules:stats")
async def admin_modules_stats(callback: CallbackQuery):
    """Статистика модулей"""
    async with aiosqlite.connect(db.db_path) as conn:
        # Всего создано
        async with conn.execute(
            "SELECT COUNT(*) FROM modules"
        ) as cursor:
            total = (await cursor.fetchone())[0]
        
        # По редкости
        async with conn.execute(
            "SELECT rarity, COUNT(*) as count FROM modules GROUP BY rarity"
        ) as cursor:
            by_rarity = await cursor.fetchall()
        
        # Установлено / в инвентаре
        async with conn.execute(
            "SELECT COUNT(*) FROM modules WHERE slot IS NOT NULL"
        ) as cursor:
            installed = (await cursor.fetchone())[0]
    
    text = (
        "📊 <b>СТАТИСТИКА МОДУЛЕЙ</b>\n\n"
        f"Всего создано: {format_number(total)}\n\n"
        "По редкости:\n"
    )
    
    rarity_names = {1: "⚪️ Обычных", 2: "🟢 Редких", 3: "🟣 Эпических", 4: "🔴 Мифических", 5: "🟡 Легендарных"}
    
    for rarity, count in sorted(by_rarity, key=lambda x: x[0]):
        text += f"{rarity_names.get(rarity, rarity)}: {format_number(count)}\n"
    
    text += f"\n🤚 Установлено: {format_number(installed)}\n"
    text += f"📦 В инвентаре: {format_number(total - installed)}\n"
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard("admin:modules"),
            parse_mode='HTML'
        )
    except:
        pass
    
    await callback.answer()


@router.callback_query(F.data == "admin:modules:test")
async def admin_modules_test(callback: CallbackQuery):
    """Тест генерации модуля"""
    text = (
        "🧪 <b>ТЕСТ ГЕНЕРАЦИИ МОДУЛЯ</b>\n\n"
        "Выбери редкость для теста:"
    )
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_module_rarity_keyboard("test_module"),
            parse_mode='HTML'
        )
    except:
        pass
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin:test_module:module:"))
async def admin_modules_test_result(callback: CallbackQuery):
    """Результат теста генерации"""
    rarity_name = callback.data.split(":")[-1]
    
    rarity_map = {
        "common": Rarity.COMMON,
        "rare": Rarity.RARE,
        "epic": Rarity.EPIC,
        "mythic": Rarity.MYTHIC,
        "legendary": Rarity.LEGENDARY
    }
    
    rarity = rarity_map.get(rarity_name, Rarity.COMMON)
    
    # Генерируем
    module = ModuleSystem.generate_module()
    module["rarity"] = rarity  # Форсируем редкость
    
    text = (
        f"🧪 <b>СГЕНЕРИРОВАН ТЕСТОВЫЙ МОДУЛЬ</b>\n\n"
        f"{RARITY_EMOJI[rarity]} {module['name']} #тест\n\n"
        f"💚 <b>Бафы:</b>\n"
    )
    
    for key, value in module['buffs'].items():
        name_buf = BUFF_NAMES.get(key, key)
        text += f"• {name_buf}: +{value}%\n"
    
    text += f"\n❤️ <b>Дебафы:</b>\n"
    for key, value in module['debuffs'].items():
        name_buf = DEBUFF_NAMES.get(key, key)
        text += f"• {name_buf}: +{value}%\n"
    
    builder = [
        [
            {"text": "🔄 Ещё", "callback_data": f"admin:test_module:module:{rarity_name}"},
            {"text": "⬅️ Назад", "callback_data": "admin:modules:test"}
        ]
    ]
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn[0]["text"], callback_data=btn[0]["callback_data"]),
         InlineKeyboardButton(text=btn[1]["text"], callback_data=btn[1]["callback_data"])]
        for btn in builder
    ])
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
    except:
        pass
    
    await callback.answer()


# ===== РАЗДЕЛ ДРОП =====

@router.callback_query(F.data == "admin:drop")
async def admin_drop_menu(callback: CallbackQuery):
    """Меню управления дропом"""
    if not await check_permission(callback.from_user.id, "drop"):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    # Получаем текущие шансы
    chances = await settings_manager.get_rarity_chances()
    
    text = (
        "🎲 <b>ШАНСЫ РЕДКОСТИ МОДУЛЕЙ</b>\n\n"
        "Текущие значения:\n\n"
        f"⚪️ Обычная: {chances.get('common', 70.0)}%\n"
        f"🟢 Редкая: {chances.get('rare', 20.0)}%\n"
        f"🟣 Эпическая: {chances.get('epic', 7.0)}%\n"
        f"🔴 Мифическая: {chances.get('mythic', 2.5)}%\n"
        f"🟡 Легендарная: {chances.get('legendary', 0.5)}%\n\n"
        f"Сумма: {sum(chances.values()):.1f}%"
    )
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_drop_menu_keyboard(),
            parse_mode='HTML'
        )
    except:
        pass
    
    await callback.answer()


@router.callback_query(F.data == "admin:drop:presets")
async def admin_drop_presets(callback: CallbackQuery):
    """Пресеты шансов"""
    text = "📋 <b>ПРЕСЕТЫ ШАНСОВ</b>"
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_rarity_presets_keyboard(),
            parse_mode='HTML'
        )
    except:
        pass
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin:drop:preset:"))
async def admin_drop_preset_apply(callback: CallbackQuery):
    """Применение пресета"""
    preset_name = callback.data.split(":")[-1]
    
    if preset_name not in RARITY_PRESETS:
        await callback.answer("❌ Пресет не найден", show_alert=True)
        return
    
    preset = RARITY_PRESETS[preset_name]
    
    # Применяем
    await settings_manager.set_rarity_chances(preset, callback.from_user.id)
    
    # Логируем
    await log_action(
        admin_id=callback.from_user.id,
        action="apply_preset",
        details=f"Preset: {preset_name}"
    )
    
    await callback.answer(f"✅ Пресет {preset_name} применён", show_alert=True)
    
    # Обновляем меню
    await admin_drop_menu(callback)


# ===== РАЗДЕЛ ЭКОНОМИКА =====

@router.callback_query(F.data == "admin:economy")
async def admin_economy_menu(callback: CallbackQuery):
    """Меню экономики"""
    if not await check_permission(callback.from_user.id, "economy"):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    # Получаем цены
    prices = await settings_manager.get_sell_prices()
    
    text = (
        "💰 <b>ЦЕНА ПРОДАЖИ МОДУЛЕЙ</b>\n\n"
        f"Базовая цена: {format_number(prices.get('base', 1500))} ⚙️\n\n"
        "Множители по редкости:\n"
    )
    
    multipliers = prices.get('multipliers', {})
    rarity_names = {"common": "⚪️ Обычный", "rare": "🟢 Редкий", "epic": "🟣 Эпический", "mythic": "🔴 Мифический", "legendary": "🟡 Легендарный"}
    
    for rarity, mult in multipliers.items():
        price = prices.get('base', 1500) * mult
        text += f"{rarity_names.get(rarity, rarity)}: ×{mult} ({format_number(int(price))} ⚙️)\n"
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_economy_menu_keyboard(),
            parse_mode='HTML'
        )
    except:
        pass
    
    await callback.answer()


# ===== РАЗДЕЛ СТАТИСТИКА =====

@router.callback_query(F.data == "admin:stats")
async def admin_stats_menu(callback: CallbackQuery):
    """Меню статистики"""
    if not await check_permission(callback.from_user.id, "stats"):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    # Собираем статистику
    async with aiosqlite.connect(db.db_path) as conn:
        # Игроки
        async with conn.execute("SELECT COUNT(*) FROM users") as cursor:
            total_players = (await cursor.fetchone())[0]
        
        async with conn.execute(
            "SELECT COUNT(*) FROM users WHERE date(last_activity) = date('now')"
        ) as cursor:
            active_today = (await cursor.fetchone())[0]
        
        async with conn.execute(
            "SELECT COUNT(*) FROM users WHERE is_banned = 1"
        ) as cursor:
            banned = (await cursor.fetchone())[0]
        
        # Ресурсы
        async with conn.execute("SELECT SUM(metal) FROM users") as cursor:
            total_metal = (await cursor.fetchone())[0] or 0
        
        async with conn.execute("SELECT SUM(crystals) FROM users") as cursor:
            total_crystals = (await cursor.fetchone())[0] or 0
        
        async with conn.execute("SELECT SUM(dark_matter) FROM users") as cursor:
            total_dm = (await cursor.fetchone())[0] or 0
        
        # Контейнеры
        async with conn.execute(
            "SELECT COUNT(*) FROM containers WHERE status = 'opened'"
        ) as cursor:
            containers_opened = (await cursor.fetchone())[0]
        
        # Модули
        async with conn.execute("SELECT COUNT(*) FROM modules") as cursor:
            modules_created = (await cursor.fetchone())[0]
    
    text = (
        "📊 <b>ОБЩАЯ СТАТИСТИКА</b>\n\n"
        "👥 <b>ИГРОКИ:</b>\n"
        f"▸ Всего зарегистрировано: {format_number(total_players)}\n"
        f"▸ Активных сегодня: {format_number(active_today)}\n"
        f"▸ Забанено: {format_number(banned)}\n\n"
        "💰 <b>ЭКОНОМИКА:</b>\n"
        f"▸ Всего металла: {format_number(total_metal)} ⚙️\n"
        f"▸ Всего кристаллов: {format_number(total_crystals)} 💎\n"
        f"▸ Всего тёмной материи: {format_number(total_dm)} 🕳️\n\n"
        "📦 <b>КОНТЕЙНЕРЫ:</b>\n"
        f"▸ Открыто всего: {format_number(containers_opened)}\n\n"
        "🧩 <b>МОДУЛИ:</b>\n"
        f"▸ Создано всего: {format_number(modules_created)}"
    )
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_stats_menu_keyboard(),
            parse_mode='HTML'
        )
    except:
        pass
    
    await callback.answer()


# ===== РАЗДЕЛ ЛОГИ =====

@router.callback_query(F.data == "admin:logs")
async def admin_logs_menu(callback: CallbackQuery):
    """Меню логов"""
    if not await check_permission(callback.from_user.id, "logs"):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    # Получаем последние логи
    async with aiosqlite.connect(db.db_path) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute(
            """SELECT al.*, u.username as admin_name
               FROM admin_logs al
               LEFT JOIN users u ON al.admin_id = u.user_id
               ORDER BY al.created_at DESC LIMIT 10"""
        ) as cursor:
            logs = await cursor.fetchall()
    
    text = "📜 <b>ЖУРНАЛ ДЕЙСТВИЙ</b>\n\n"
    
    if not logs:
        text += "Нет записей"
    else:
        for log in logs:
            time = log['created_at'][:16] if log['created_at'] else 'N/A'
            admin = log['admin_name'] or str(log['admin_id'])
            action = log['action']
            text += f"{time} @{admin} {action}\n"
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_logs_menu_keyboard(),
            parse_mode='HTML'
        )
    except:
        pass
    
    await callback.answer()


# ===== РАЗДЕЛ ТЕСТИРОВАНИЕ =====

@router.callback_query(F.data == "admin:testing")
async def admin_testing_menu(callback: CallbackQuery):
    """Меню тестирования"""
    if not await check_permission(callback.from_user.id, "testing"):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    text = "🧪 <b>ТЕСТИРОВАНИЕ</b>"
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_testing_menu_keyboard(),
            parse_mode='HTML'
        )
    except:
        pass
    
    await callback.answer()


# ===== РАЗДЕЛ НАСТРОЙКИ =====

@router.callback_query(F.data == "admin:settings")
async def admin_settings_menu(callback: CallbackQuery):
    """Меню настроек"""
    if not await check_permission(callback.from_user.id, "settings"):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    text = "⚙️ <b>НАСТРОЙКИ</b>"
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_settings_menu_keyboard(),
            parse_mode='HTML'
        )
    except:
        pass
    
    await callback.answer()


@router.callback_query(F.data == "admin:settings:admins")
async def admin_settings_admins(callback: CallbackQuery):
    """Управление администраторами"""
    if not await check_permission(callback.from_user.id, "settings"):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    # Получаем список админов
    async with aiosqlite.connect(db.db_path) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute(
            """SELECT a.user_id, a.role, u.username
               FROM admins a
               LEFT JOIN users u ON a.user_id = u.user_id
               ORDER BY 
               CASE a.role
                   WHEN 'owner' THEN 1
                   WHEN 'senior' THEN 2
                   WHEN 'moderator' THEN 3
                   WHEN 'support' THEN 4
               END"""
        ) as cursor:
            admins = await cursor.fetchall()
    
    text = "👥 <b>УПРАВЛЕНИЕ АДМИНИСТРАТОРАМИ</b>\n\nСписок администраторов:\n\n"
    
    for admin in admins:
        role_emoji = ROLE_EMOJI.get(admin['role'], '🔹')
        role_name = ROLE_NAMES.get(admin['role'], admin['role'])
        username = admin['username'] or str(admin['user_id'])
        text += f"{role_emoji} @{username} ({role_name})\n"
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard("admin:settings"),
            parse_mode='HTML'
        )
    except:
        pass
    
    await callback.answer()


# ===== РАЗДЕЛ СОБЫТИЯ =====

@router.callback_query(F.data == "admin:events")
async def admin_events_menu(callback: CallbackQuery):
    """Меню событий"""
    if not await check_permission(callback.from_user.id, "events"):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    # Проверяем активные события
    async with aiosqlite.connect(db.db_path) as conn:
        async with conn.execute(
            "SELECT COUNT(*) FROM admin_events WHERE status = 'active'"
        ) as cursor:
            has_active = (await cursor.fetchone())[0] > 0
    
    text = "🎉 <b>СОБЫТИЯ</b>"
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_events_menu_keyboard(has_active),
            parse_mode='HTML'
        )
    except:
        pass
    
    await callback.answer()


@router.callback_query(F.data == "admin:events:create")
async def admin_events_create(callback: CallbackQuery):
    """Создание ивента"""
    text = (
        "🎉 <b>СОЗДАНИЕ ИВЕНТА</b>\n\n"
        "Тип ивента:"
    )
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_event_type_keyboard(),
            parse_mode='HTML'
        )
    except:
        pass
    
    await callback.answer()


# ===== РАЗДЕЛ БЭКАПЫ =====

@router.callback_query(F.data == "admin:backups")
async def admin_backups_menu(callback: CallbackQuery):
    """Меню бэкапов"""
    if not await check_permission(callback.from_user.id, "backups"):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    # Проверяем наличие бэкапов
    backup_dir = "backups"
    has_backups = os.path.exists(backup_dir) and len(os.listdir(backup_dir)) > 0
    
    # Последний бэкап
    last_backup = "N/A"
    last_size = 0
    
    if has_backups:
        files = sorted(
            [f for f in os.listdir(backup_dir) if f.endswith('.db')],
            key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)),
            reverse=True
        )
        if files:
            last_backup = files[0]
            last_size = os.path.getsize(os.path.join(backup_dir, last_backup))
    
    text = (
        "💾 <b>УПРАВЛЕНИЕ БЭКАПАМИ</b>\n\n"
        f"Последний бэкап: {last_backup}\n"
        f"Размер: {last_size / 1024 / 1024:.1f} MB" if last_size else ""
    )
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_backups_menu_keyboard(has_backups),
            parse_mode='HTML'
        )
    except:
        pass
    
    await callback.answer()


@router.callback_query(F.data == "admin:backups:create")
async def admin_backups_create(callback: CallbackQuery):
    """Создание бэкапа"""
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_name)
    
    try:
        shutil.copy2(db.db_path, backup_path)
        backup_size = os.path.getsize(backup_path)
        
        # Логируем
        await log_action(
            admin_id=callback.from_user.id,
            action="create_backup",
            details=f"{backup_name} ({backup_size / 1024 / 1024:.1f} MB)"
        )
        
        await callback.answer(
            f"✅ Бэкап создан: {backup_name}",
            show_alert=True
        )
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)[:50]}", show_alert=True)
    
    await admin_backups_menu(callback)


# ===== РАЗДЕЛ МЕТРИКИ =====

@router.callback_query(F.data == "admin:metrics")
async def admin_metrics_menu(callback: CallbackQuery):
    """Меню метрик"""
    if not await check_permission(callback.from_user.id, "metrics"):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    import psutil
    import os
    
    # Получаем метрики
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    db_size = os.path.getsize(db.db_path) if os.path.exists(db.db_path) else 0
    
    text = (
        "📈 <b>ТЕХНИЧЕСКИЕ МЕТРИКИ</b>\n\n"
        "🧠 <b>ПАМЯТЬ:</b>\n"
        f"▸ Использовано RAM: {memory_info.rss / 1024 / 1024:.1f} MB\n\n"
        "💾 <b>БАЗА ДАННЫХ:</b>\n"
        f"▸ Размер: {db_size / 1024 / 1024:.1f} MB\n\n"
        "👥 <b>ПОЛЬЗОВАТЕЛИ:</b>\n"
    )
    
    # Активные пользователи
    async with aiosqlite.connect(db.db_path) as conn:
        async with conn.execute(
            "SELECT COUNT(*) FROM users WHERE datetime(last_activity) > datetime('now', '-5 minutes')"
        ) as cursor:
            online = (await cursor.fetchone())[0]
    
    text += f"▸ Онлайн сейчас: {online}"
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_metrics_keyboard(),
            parse_mode='HTML'
        )
    except:
        pass
    
    await callback.answer()


# ===== МАССОВЫЕ ОПЕРАЦИИ =====

@router.callback_query(F.data == "admin:players:mass")
async def admin_mass_operations(callback: CallbackQuery):
    """Меню массовых операций"""
    if not await check_permission(callback.from_user.id, "players"):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    text = "👥 <b>МАССОВЫЕ ОПЕРАЦИИ</b>"
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_mass_operations_keyboard(),
            parse_mode='HTML'
        )
    except:
        pass
    
    await callback.answer()


@router.callback_query(F.data == "admin:players:mass:container")
async def admin_mass_container(callback: CallbackQuery):
    """Массовая выдача контейнеров - выбор типа"""
    text = (
        "👥 <b>МАССОВАЯ ВЫДАЧА КОНТЕЙНЕРОВ</b>\n\n"
        "Выбери тип контейнера:"
    )
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_container_type_keyboard("mass_container"),
            parse_mode='HTML'
        )
    except:
        pass
    
    await callback.answer()


# ===== Пагинация материалов =====

@router.callback_query(F.data.startswith("admin:materials:page:"))
async def admin_materials_page(callback: CallbackQuery):
    """Пагинация материалов"""
    page = int(callback.data.split(":")[-1])
    
    text = (
        "🧱 <b>УПРАВЛЕНИЕ МАТЕРИАЛАМИ</b>\n\n"
        "Выбери материал:"
    )
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_materials_keyboard(page),
            parse_mode='HTML'
        )
    except:
        pass
    
    await callback.answer()
