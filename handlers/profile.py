from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from database import db
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


@router.message(Command('profile'))
@router.message(F.text == '👤 Профиль')
async def cmd_profile(message: Message):
    await show_profile_screen(message, message.from_user.id)


async def show_profile_screen(message_or_callback, user_id: int, edit: bool = False):
    from aiogram.types import Message
    user = await db.get_user(user_id)

    if not user:
        if isinstance(message_or_callback, Message):
            await message_or_callback.answer('Ошибка: пользователь не найден')
        return

    level = user.get('level', 1)
    exp = user.get('experience', 0)
    exp_needed = level * 1000

    text = (
        f'👤 <b>ПРОФИЛЬ ИГРОКА</b>\n\n'
        f"▸ Ник: @{user.get('username', 'Неизвестно')}\n"
        f'▸ ID: <code>{user_id}</code>\n'
        f'▸ Уровень: {level} (опыт: {exp:,} / {exp_needed:,})\n'
        f"▸ Престиж: {user.get('prestige', 0)}\n\n"
        f'📊 <b>СТАТИСТИКА:</b>\n'
        f"▸ Всего добыто: {user.get('total_mined', 0):,} ресурсов\n"
        f"▸ Всего кликов: {user.get('total_clicks', 0):,}\n\n"
        f'💰 <b>БАЛАНС:</b>\n'
        f"▸ Кредиты: {user.get('credits', 0):,}\n"
        f"▸ Квант-токены: {user.get('quantum_tokens', 0)}"
    )

    keyboard = [
        [
            InlineKeyboardButton(text='🏅 Достижения', callback_data='achievements'),
            InlineKeyboardButton(text='📊 Детально', callback_data='detailed_stats'),
            InlineKeyboardButton(text='⚙️ Настройки', callback_data='settings')
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
    text = (
        '🏅 <b>ДОСТИЖЕНИЯ</b>\n\n'
        '🏆 <b>Первый миллион</b> — Добыть 1,000,000 ресурсов\n'
        '🏆 <b>Коллекционер</b> — Собрать 50 предметов\n'
        '🏆 <b>Ударник труда</b> — Сделать 1,000 кликов\n'
        '🏆 <b>Капиталист</b> — Заработать 100,000 кредитов'
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='◀️ Назад', callback_data='refresh_profile')]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
    await callback.answer()
