from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


@router.message(Command('craft'))
@router.message(F.text == '🔨 Крафт')
async def cmd_craft(message: Message):
    text = (
        '🔨 <b>КРАФТ-СТАНЦИЯ</b>\n'
        'Доступные рецепты: 0/45\n\n'
        '<i>Пока нет доступных рецептов.</i>\n\n'
        'Собирай ресурсы и предметы!'
    )

    keyboard = [
        [
            InlineKeyboardButton(text='⚙️ Модули', callback_data='craft_modules'),
            InlineKeyboardButton(text='🤖 Дроны', callback_data='craft_drones')
        ],
        [InlineKeyboardButton(text='◀️ Назад', callback_data='back_to_menu')]
    ]

    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode='HTML')
