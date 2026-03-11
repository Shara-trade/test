from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


@router.message(Command('clan'))
@router.message(F.text == '👥 Клан')
async def cmd_clan(message: Message):
    text = (
        '👥 <b>КОРПОРАЦИИ</b>\n\n'
        'Ты пока не состоишь в корпорации.\n\n'
        '<b>Корпорации дают:</b>\n'
        '▸ Общий склад ресурсов\n'
        '▸ Клановые бонусы (+5% к добыче)\n'
        '▸ Участие в рейдах на боссов\n'
        '▸ Клановый чат\n\n'
        '<b>Стоимость создания:</b> 10,000 металла'
    )

    keyboard = [
        [InlineKeyboardButton(text='🔍 Найти корпорацию', callback_data='clan_search')],
        [InlineKeyboardButton(text='➕ Создать корпорацию', callback_data='clan_create')],
        [InlineKeyboardButton(text='🏆 Топ корпораций', callback_data='top_clans')],
        [InlineKeyboardButton(text='◀️ Назад', callback_data='back_to_menu')]
    ]

    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode='HTML')
