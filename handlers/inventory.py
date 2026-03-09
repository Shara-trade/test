from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


@router.message(Command('inventory'))
@router.message(F.text == '📦 Инвентарь')
async def cmd_inventory(message: Message):
    text = (
        '📦 <b>ТВОЙ ИНВЕНТАРЬ</b>\n'
        'Предметов: 0/100\n\n'
        '<i>Инвентарь пока пуст.</i>\n\n'
        'Добывай астероиды, чтобы найти предметы!\n'
        'Шанс выпадения: 5% за клик'
    )

    keyboard = [
        [
            InlineKeyboardButton(text='🔹 Все', callback_data='inv_all'),
            InlineKeyboardButton(text='🔸 Редкие', callback_data='inv_rare')
        ],
        [
            InlineKeyboardButton(text='📤 На рынок', callback_data='inv_market'),
            InlineKeyboardButton(text='◀️ Назад', callback_data='back_to_menu')
        ]
    ]

    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode='HTML')


@router.callback_query(F.data == 'back_to_menu')
async def on_back_to_menu(callback: CallbackQuery):
    from handlers.start import welcome_back_user
    from database import db
    user = await db.get_user(callback.from_user.id)
    await welcome_back_user(callback.message, user)
    await callback.answer()
