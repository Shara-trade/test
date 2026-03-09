from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


@router.message(Command('market'))
@router.message(F.text == '🏪 Рынок')
async def cmd_market(message: Message):
    text = (
        '🏪 <b>РЫНОК ИГРОКОВ</b>\n'
        'Активных лотов: 0\n\n'
        '📊 <b>КАТЕГОРИИ:</b>\n'
        '▸ 🤖 Дроны (0 лотов)\n'
        '▸ ⚙️ Модули (0 лотов)\n'
        '▸ 💎 Артефакты (0 лотов)\n\n'
        '<i>Рынок пока пуст.</i>'
    )

    keyboard = [
        [
            InlineKeyboardButton(text='🤖 Дроны', callback_data='market_drones'),
            InlineKeyboardButton(text='⚙️ Модули', callback_data='market_modules')
        ],
        [
            InlineKeyboardButton(text='➕ ВЫСТАВИТЬ ЛОТ', callback_data='market_sell')
        ],
        [InlineKeyboardButton(text='◀️ Назад', callback_data='back_to_menu')]
    ]

    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode='HTML')
