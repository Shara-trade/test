"""
Топ игроков.
Реальные данные из базы данных с пагинацией и кэшированием.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import aiosqlite

from database import db
from database.query_cache import get_cached_top, set_cached_top, get_cached_user_rank, set_cached_user_rank
from handlers.utils import Paginator, format_number

router = Router()

# Категории топов
CATEGORIES = {
    'level': {
        'name': '🏆 По уровню',
        'order': 'level DESC, experience DESC',
        'fields': 'user_id, username, level, experience'
    },
    'mining': {
        'name': '⛏ По добыче',
        'order': 'total_mined DESC',
        'fields': 'user_id, username, total_mined'
    },
    'wealth': {
        'name': '💰 По богатству',
        'order': '(metal + crystals * 10 + dark_matter * 100) DESC',
        'fields': 'user_id, username, metal, crystals, dark_matter'
    },
    'clicks': {
        'name': '👆 По кликам',
        'order': 'total_clicks DESC',
        'fields': 'user_id, username, total_clicks'
    }
}


async def get_top_players(category: str, limit: int = 10, offset: int = 0) -> list:
    """
    Получить топ игроков из БД с кэшированием.
    
    Args:
        category: Категория (level, mining, wealth, clicks)
        limit: Количество записей
        offset: Смещение для пагинации
    
    Returns:
        Список словарей с данными игроков
    """
    # Проверяем кэш (страница = offset // limit + 1)
    page = offset // limit + 1
    cached = await get_cached_top(category, page, limit)
    
    if cached is not None:
        return cached
    
    cat_info = CATEGORIES.get(category, CATEGORIES['level'])
    
    async with aiosqlite.connect(db.db_path) as conn:
        conn.row_factory = aiosqlite.Row
        
        query = f"""
            SELECT {cat_info['fields']}
            FROM users
            WHERE is_banned = 0
            ORDER BY {cat_info['order']}
            LIMIT ? OFFSET ?
        """
        
        async with conn.execute(query, (limit, offset)) as cursor:
            rows = await cursor.fetchall()
            result = [dict(row) for row in rows]
    
    # Кэшируем на 5 минут
    await set_cached_top(category, page, result, limit)
    
    return result


async def get_total_players() -> int:
    """Получить общее количество игроков"""
    async with aiosqlite.connect(db.db_path) as conn:
        async with conn.execute(
            "SELECT COUNT(*) FROM users WHERE is_banned = 0"
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def get_user_rank(user_id: int, category: str) -> int:
    """
    Получить ранг пользователя в категории с кэшированием.
    
    Returns:
        Позиция в топе (1-based)
    """
    # Проверяем кэш
    cached = await get_cached_user_rank(user_id, category)
    
    if cached is not None:
        return cached
    
    cat_info = CATEGORIES.get(category, CATEGORIES['level'])
    
    async with aiosqlite.connect(db.db_path) as conn:
        if category == 'level':
            query = """
                SELECT COUNT(*) + 1 as rank FROM users 
                WHERE is_banned = 0 
                AND (
                    level > (SELECT level FROM users WHERE user_id = ?)
                    OR (level = (SELECT level FROM users WHERE user_id = ?) 
                        AND experience > (SELECT experience FROM users WHERE user_id = ?))
                )
            """
            params = (user_id, user_id, user_id)
        
        elif category == 'mining':
            query = """
                SELECT COUNT(*) + 1 as rank FROM users 
                WHERE is_banned = 0 
                AND total_mined > (SELECT COALESCE(total_mined, 0) FROM users WHERE user_id = ?)
            """
            params = (user_id,)
        
        elif category == 'wealth':
            query = """
                SELECT COUNT(*) + 1 as rank FROM users 
                WHERE is_banned = 0 
                AND (metal + crystals * 10 + dark_matter * 100) > 
                    (SELECT COALESCE(metal, 0) + COALESCE(crystals, 0) * 10 + COALESCE(dark_matter, 0) * 100 
                     FROM users WHERE user_id = ?)
            """
            params = (user_id,)
        
        elif category == 'clicks':
            query = """
                SELECT COUNT(*) + 1 as rank FROM users 
                WHERE is_banned = 0 
                AND total_clicks > (SELECT COALESCE(total_clicks, 0) FROM users WHERE user_id = ?)
            """
            params = (user_id,)
        
        else:
            return 0
        
        async with conn.execute(query, params) as cursor:
            row = await cursor.fetchone()
            rank = row[0] if row else 0
    
    # Кэшируем на 1 минуту
    await set_cached_user_rank(user_id, category, rank)
    
    return rank


def format_top_entry(player: dict, rank: int, category: str) -> str:
    """Форматировать запись топа"""
    username = player.get('username') or f"Игрок {player['user_id']}"
    
    # Медали для топ-3
    medals = {1: '🥇', 2: '🥈', 3: '🥉'}
    medal = medals.get(rank, f"{rank}.")
    
    if category == 'level':
        level = player.get('level', 1)
        exp = player.get('experience', 0)
        return f"{medal} @{username} — Ур. {level} ({format_number(exp)} опыта)"
    
    elif category == 'mining':
        mined = player.get('total_mined', 0)
        return f"{medal} @{username} — {format_number(mined)} mined"
    
    elif category == 'wealth':
        metal = player.get('metal', 0)
        crystals = player.get('crystals', 0)
        dm = player.get('dark_matter', 0)
        total = metal + crystals * 10 + dm * 100
        return f"{medal} @{username} — {format_number(total)} 💰"
    
    elif category == 'clicks':
        clicks = player.get('total_clicks', 0)
        return f"{medal} @{username} — {format_number(clicks)} кликов"
    
    return f"{medal} @{username}"


@router.message(Command('top'))
@router.message(F.text == '📊 Топ')
async def cmd_top(message: Message):
    await show_top_screen(message, message.from_user.id)


async def show_top_screen(
    message_or_callback, 
    user_id: int, 
    edit: bool = False, 
    category: str = 'level',
    page: int = 1
):
    """
    Показать экран топа.
    
    Args:
        message_or_callback: Message или CallbackQuery.message
        user_id: ID пользователя
        edit: Режим редактирования
        category: Категория топа
        page: Номер страницы
    """
    from aiogram.types import Message
    
    # Получаем данные пользователя
    user = await db.get_user(user_id)
    if not user:
        if isinstance(message_or_callback, Message):
            await message_or_callback.answer('Ошибка: пользователь не найден')
        return
    
    # Получаем топ игроков
    per_page = 10
    offset = (page - 1) * per_page
    
    top_players = await get_top_players(category, per_page, offset)
    total_players = await get_total_players()
    total_pages = max(1, (total_players + per_page - 1) // per_page)
    
    # Получаем ранг пользователя
    user_rank = await get_user_rank(user_id, category)
    
    # Формируем текст
    cat_info = CATEGORIES.get(category, CATEGORIES['level'])
    
    text = f"📊 <b>ТОП ИГРОКОВ</b>\n\n"
    text += f"{cat_info['name']}:\n\n"
    
    if not top_players:
        text += "Пока нет данных"
    else:
        start_rank = offset + 1
        for i, player in enumerate(top_players):
            rank = start_rank + i
            text += format_top_entry(player, rank, category) + "\n"
    
    # Информация о позиции пользователя
    text += f"\n🏅 Твоя позиция: #{user_rank}"
    
    # Клавиатура
    builder = InlineKeyboardBuilder()
    
    # Кнопки категорий
    cat_buttons = []
    for cat_key, cat_info in CATEGORIES.items():
        if cat_key == category:
            cat_buttons.append({"text": f"✓ {cat_info['name'].split()[0]}", "callback_data": "noop"})
        else:
            cat_buttons.append({"text": cat_info['name'].split()[0], "callback_data": f"top_{cat_key}"})
    
    for btn in cat_buttons:
        builder.button(**btn)
    builder.adjust(2)
    
    # Навигация по страницам
    if total_pages > 1:
        nav_buttons = []
        
        if page > 1:
            nav_buttons.append({"text": "◀️", "callback_data": f"top_page_{category}_{page - 1}"})
        
        nav_buttons.append({"text": f"{page}/{total_pages}", "callback_data": "noop"})
        
        if page < total_pages:
            nav_buttons.append({"text": "▶️", "callback_data": f"top_page_{category}_{page + 1}"})
        
        for btn in nav_buttons:
            builder.button(**btn)
        builder.adjust(3)
    
    # Кнопка "Назад"
    builder.button(text="◀️ В меню", callback_data="back_to_menu_from_top")
    builder.adjust(1)
    
    reply_markup = builder.as_markup()
    
    # Отправляем/редактируем
    if edit and hasattr(message_or_callback, 'edit_text'):
        try:
            await message_or_callback.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
        except:
            await message_or_callback.answer(text, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await message_or_callback.answer(text, reply_markup=reply_markup, parse_mode='HTML')


@router.callback_query(F.data.startswith('top_'))
async def on_top_category(callback: CallbackQuery):
    """Обработка выбора категории"""
    data = callback.data
    
    if data.startswith('top_page_'):
        # Пагинация: top_page_level_2
        parts = data.split('_')
        if len(parts) >= 4:
            category = parts[2]
            page = int(parts[3])
        else:
            category = 'level'
            page = 1
    else:
        # Категория: top_level
        category = data.replace('top_', '')
        page = 1
    
    if category not in CATEGORIES:
        category = 'level'
    
    await show_top_screen(callback.message, callback.from_user.id, edit=True, category=category, page=page)
    await callback.answer()


@router.callback_query(F.data == 'refresh_top')
async def on_refresh_top(callback: CallbackQuery):
    """Обновить топ"""
    await show_top_screen(callback.message, callback.from_user.id, edit=True)
    await callback.answer()


@router.callback_query(F.data == 'back_to_menu_from_top')
async def on_back_to_menu(callback: CallbackQuery):
    """Возврат в меню"""
    from handlers.start import welcome_back_user
    user = await db.get_user(callback.from_user.id)
    await welcome_back_user(callback.message, user)
    await callback.answer()
