from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from database import db
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Игровые системы
from game import LevelSystem

router = Router()


@router.message(Command('profile'))
@router.message(F.text == '👤 Профиль')
async def cmd_profile(message: Message):
    await show_profile_screen(message, message.from_user.id)


async def show_profile_screen(message_or_callback, user_id: int, edit: bool = False):
    from aiogram.types import Message
    
    # Получаем полную статистику
    stats = await db.get_user_stats(user_id)

    if not stats:
        if isinstance(message_or_callback, Message):
            await message_or_callback.answer('Ошибка: пользователь не найден')
        return

    level = stats.get('level', 1)
    experience = stats.get('experience', 0)
    prestige = stats.get('prestige', 0)
    tech_tokens = stats.get('tech_tokens', 0)
    
    # Информация об уровне
    level_info = LevelSystem.get_progress_info(level, experience)
    
    # Ранг игрока
    rank_level = await db.get_user_rank(user_id, "level")
    rank_mined = await db.get_user_rank(user_id, "mined")
    
    text = (
        f'👤 <b>ПРОФИЛЬ ИГРОКА</b>\n\n'
        f"▸ Ник: @{stats.get('username', 'Неизвестно')}\n"
        f'▸ ID: <code>{user_id}</code>\n\n'
        
        f'📈 <b>ПРОГРЕСС:</b>\n'
        f'▸ Уровень: {level} "{level_info["title"]}"\n'
        f'▸ Опыт: {experience:,} / {level_info["exp_needed"]:,} [{level_info["exp_bar"]}] {level_info["exp_percent"]}%\n'
        f'▸ Престиж: {prestige}\n'
        f'▸ Tech-токены: {tech_tokens}\n\n'
        
        f'📊 <b>СТАТИСТИКА:</b>\n'
        f"▸ Всего добыто: {stats.get('total_mined', 0):,} ресурсов\n"
        f"▸ Всего кликов: {stats.get('total_clicks', 0):,}\n"
        f"▸ Дронов: {stats.get('drones_count', 0)} / 50\n"
        f"▸ Предметов: {stats.get('items_count', 0)}\n"
        f'▸ Ранг по уровню: #{rank_level}\n'
        f'▸ Ранг по добыче: #{rank_mined}\n\n'
        
        f'💰 <b>РЕСУРСЫ:</b>\n'
        f"▸ Металл: {stats.get('metal', 0):,} ⚙️\n"
        f"▸ Кристаллы: {stats.get('crystals', 0):,} 💎\n"
        f"▸ Тёмная материя: {stats.get('dark_matter', 0):,} ⚫\n\n"
        
        f'💵 <b>ВАЛЮТА:</b>\n'
        f"▸ Кредиты: {stats.get('credits', 0):,}\n"
        f"▸ Квант-токены: {stats.get('quantum_tokens', 0)}\n\n"
        
        f'⚡ <b>ЭНЕРГИЯ:</b>\n'
        f"▸ {stats.get('energy', 0):,} / {stats.get('max_energy', 1000):,}\n"
    )

    # Бонусы от уровня
    mining_bonus = int((LevelSystem.get_mining_bonus(level) - 1) * 100)
    energy_bonus = LevelSystem.get_max_energy_bonus(level)
    
    text += (
        f'\n🎁 <b>БОНУСЫ ОТ УРОВНЯ:</b>\n'
        f'▸ К добыче: +{mining_bonus}%\n'
        f'▸ К макс. энергии: +{energy_bonus}'
    )

    keyboard = [
        [
            InlineKeyboardButton(text='🏅 Достижения', callback_data='achievements'),
            InlineKeyboardButton(text='📊 Детально', callback_data='detailed_stats'),
        ],
        [
            InlineKeyboardButton(text='🔄 Обновить', callback_data='refresh_profile'),
            InlineKeyboardButton(text='◀️ Назад', callback_data='back_to_menu_from_profile')
        ]
    ]

    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    if edit and isinstance(message_or_callback, Message):
        try:
            await message_or_callback.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
        except:
            await message_or_callback.answer(text, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await message_or_callback.answer(text, reply_markup=reply_markup, parse_mode='HTML')


@router.callback_query(F.data == 'refresh_profile')
async def on_refresh_profile(callback: CallbackQuery):
    await callback.answer('Обновляем...')
    await show_profile_screen(callback.message, callback.from_user.id, edit=True)


@router.callback_query(F.data == 'back_to_menu_from_profile')
async def on_back_to_menu(callback: CallbackQuery):
    from handlers.start import welcome_back_user
    user = await db.get_user(callback.from_user.id)
    await welcome_back_user(callback.message, user)
    await callback.answer()


@router.callback_query(F.data == 'achievements')
async def on_achievements(callback: CallbackQuery):
    user_id = callback.from_user.id
    stats = await db.get_user_stats(user_id)
    
    total_mined = stats.get('total_mined', 0)
    total_clicks = stats.get('total_clicks', 0)
    credits = stats.get('credits', 0)
    items_count = stats.get('items_count', 0)
    
    # Проверка достижений
    achievements = [
        {
            "name": "Первый шаг",
            "desc": "Сделать первый клик",
            "done": total_clicks >= 1,
            "progress": min(1, total_clicks)
        },
        {
            "name": "Ударник труда",
            "desc": "Сделать 1,000 кликов",
            "done": total_clicks >= 1000,
            "progress": min(1000, total_clicks)
        },
        {
            "name": "Мастер клика",
            "desc": "Сделать 10,000 кликов",
            "done": total_clicks >= 10000,
            "progress": min(10000, total_clicks)
        },
        {
            "name": "Первый миллион",
            "desc": "Добыть 1,000,000 ресурсов",
            "done": total_mined >= 1000000,
            "progress": min(1000000, total_mined)
        },
        {
            "name": "Богач",
            "desc": "Иметь 100,000 кредитов",
            "done": credits >= 100000,
            "progress": min(100000, credits)
        },
        {
            "name": "Коллекционер",
            "desc": "Собрать 10 предметов",
            "done": items_count >= 10,
            "progress": min(10, items_count)
        },
    ]
    
    # Формируем текст
    text = '🏅 <b>ДОСТИЖЕНИЯ</b>\n\n'
    
    for ach in achievements:
        status = '✅' if ach['done'] else '⬜'
        target = ach['desc'].split()[-1].replace(',', '')
        
        if ach['done']:
            text += f'{status} <b>{ach["name"]}</b>\n   {ach["desc"]}\n\n'
        else:
            text += f'{status} <b>{ach["name"]}</b>\n   {ach["desc"]} ({ach["progress"]:,}/{target:,})\n\n'

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='◀️ Назад', callback_data='refresh_profile')]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
    await callback.answer()


@router.callback_query(F.data == 'detailed_stats')
async def on_detailed_stats(callback: CallbackQuery):
    user_id = callback.from_user.id
    stats = await db.get_user_stats(user_id)
    
    text = (
        f'📊 <b>ДЕТАЛЬНАЯ СТАТИСТИКА</b>\n\n'
        
        f'⛏ <b>ДОБЫЧА:</b>\n'
        f"▸ Металл: {stats.get('metal', 0):,}\n"
        f"▸ Кристаллы: {stats.get('crystals', 0):,}\n"
        f"▸ Тёмная материя: {stats.get('dark_matter', 0):,}\n"
        f"▸ Всего добыто: {stats.get('total_mined', 0):,}\n\n"
        
        f'⚡ <b>ЭНЕРГИЯ:</b>\n'
        f"▸ Текущая: {stats.get('energy', 0):,}\n"
        f"▸ Максимальная: {stats.get('max_energy', 1000):,}\n"
        f"▸ Перегрев: {stats.get('heat', 0)}%\n\n"
        
        f'🤖 <b>ДРОНЫ:</b>\n'
        f"▸ Количество: {stats.get('drones_count', 0)}\n"
        f"▸ Доход/тик: {stats.get('drones_income', 0):,}\n\n"
        
        f'📦 <b>ИНВЕНТАРЬ:</b>\n'
        f"▸ Предметов: {stats.get('items_count', 0)}\n"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='◀️ Назад', callback_data='refresh_profile')]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
    await callback.answer()
