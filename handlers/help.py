from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


@router.message(Command('help'))
async def cmd_help(message: Message):
    await show_help_screen(message)


async def show_help_screen(message_or_callback, edit: bool = False):
    text = (
        '📖 <b>ПОМОЩЬ И FAQ</b>\n\n'
        '<b>❓ КАК ИГРАТЬ?</b>\n'
        'Нажимай ⛏ Шахта и кликай по астероидам. '
        'Добывай ресурсы, покупай дронов, прокачивайся.\n\n'
        '<b>❓ ЧТО ДАЮТ ДРОНЫ?</b>\n'
        'Дроны добывают ресурсы автоматически каждые 5 секунд, '
        'даже когда ты не в игре.\n\n'
        '<b>❓ КАК ПОЛУЧИТЬ РЕДКИЕ ПРЕДМЕТЫ?</b>\n'
        'Шанс выпадения есть при каждом клике. '
        'Также предметы выпадают из контейнеров и с боссов.\n\n'
        '<b>❓ ЧТО ТАКОЕ ПРЕСТИЖ?</b>\n'
        'Достигнув 1 млрд ресурсов, ты можешь начать заново с постоянными бонусами.'
    )

    keyboard = [
        [
            InlineKeyboardButton(text='📋 Полный гайд', callback_data='full_guide'),
            InlineKeyboardButton(text='👨‍💻 Поддержка', callback_data='support')
        ],
        [
            InlineKeyboardButton(text='⚖️ Правила', callback_data='rules'),
            InlineKeyboardButton(text='◀️ Назад', callback_data='back_to_menu_from_help')
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


@router.callback_query(F.data == 'back_to_menu_from_help')
async def on_back_to_menu(callback: CallbackQuery):
    from handlers.start import welcome_back_user
    from database import db
    user = await db.get_user(callback.from_user.id)
    await welcome_back_user(callback.message, user)
    await callback.answer()
