from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from database import db
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


@router.message(Command('top'))
@router.message(F.text == '📊 Топ')
async def cmd_top(message: Message):
    await show_top_screen(message, message.from_user.id)


async def show_top_screen(message_or_callback, user_id: int, edit: bool = False, category: str = 'level'):
    from aiogram.types import Message

    user = await db.get_user(user_id)
    if not user:
        if isinstance(message_or_callback, Message):
            await message_or_callback.answer('Ошибка: пользователь не найден')
        return

    text = '📊 <b>ТОП ИГРОКОВ</b>\n\n'

    if category == 'level':
        text += '🏆 <b>ПО УРОВНЮ:</b>\n'
        text += '1. 👑 @cosmo_king — Ур. 45\n'
        text += '2. ⭐ @star_tycoon — Ур. 42\n'
        text += '3. @miner_pro — Ур. 40\n\n'
        text += f"🏅 Ты: #47 (Ур. {user.get('level', 1)})"

    elif category == 'mining':
        text += '🏅 <b>ПО ДОБЫЧЕ:</b>\n'
        text += '1. @cosmo_king — 5.2M\n'
        text += '2. @star_tycoon — 4.8M\n'
        text += '3. @miner_pro — 4.5M\n\n'
        text += f"🏅 Ты: #52 ({user.get('total_mined', 0):,})"

    keyboard = [
        [
            InlineKeyboardButton(text='📊 Уровень', callback_data='top_level'),
            InlineKeyboardButton(text='⛏ Добыча', callback_data='top_mining'),
            InlineKeyboardButton(text='💰 Богатство', callback_data='top_wealth')
        ],
        [
            InlineKeyboardButton(text='👥 Кланы', callback_data='top_clans'),
            InlineKeyboardButton(text='🔄 Обновить', callback_data='refresh_top'),
            InlineKeyboardButton(text='◀️ Назад', callback_data='back_to_menu_from_top')
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


@router.callback_query(F.data == 'top_level')
async def on_top_level(callback: CallbackQuery):
    await show_top_screen(callback.message, callback.from_user.id, edit=True, category='level')
    await callback.answer()


@router.callback_query(F.data == 'top_mining')
async def on_top_mining(callback: CallbackQuery):
    await show_top_screen(callback.message, callback.from_user.id, edit=True, category='mining')
    await callback.answer()


@router.callback_query(F.data == 'back_to_menu_from_top')
async def on_back_to_menu(callback: CallbackQuery):
    from handlers.start import welcome_back_user
    user = await db.get_user(callback.from_user.id)
    await welcome_back_user(callback.message, user)
    await callback.answer()
