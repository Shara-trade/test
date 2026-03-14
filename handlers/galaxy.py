from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


@router.message(Command('galaxy'))
@router.message(F.text == '🌌 Галактика')
async def cmd_galaxy(message: Message):
    text = (
        '🌌 <b>КАРТА ГАЛАКТИКИ</b>\n\n'
        'Текущая система: <b>Альфа-7</b>\n\n'
        '<b>Доступные системы:</b>\n\n'
        '🟢 <b>Альфа-7</b> — ДОСТУПНА\n'
        ' Ресурсы: Металл +50%, Кристаллы +20%\n\n'
        '🟡 <b>Пояс Кеплера</b> — Требуется Уровень 5\n'
        ' Ресурсы: Кристаллы +100%\n\n'
        '🔴 <b>Туманность Омега</b> — Требуется Уровень 15'
    )

    keyboard = [
        [
            InlineKeyboardButton(text='⬅️ Пред.', callback_data='galaxy_prev'),
            InlineKeyboardButton(text='📍 Текущая', callback_data='galaxy_current'),
            InlineKeyboardButton(text='➡️ След.', callback_data='galaxy_next')
        ],
        [
            InlineKeyboardButton(text='🔓 Открыть систему', callback_data='galaxy_unlock'),
            InlineKeyboardButton(text='◀️ Назад', callback_data='back_to_menu')
        ]
    ]

    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode='HTML')
