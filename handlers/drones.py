from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from database import db
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

DRONE_TYPES = {
    'basic': {'name': '🤖 Базовый дрон', 'income': 2, 'slots': 1, 'price_metal': 100},
    'miner': {'name': '⚡ Шахтёр', 'income': 8, 'slots': 2, 'price_metal': 500},
    'laser': {'name': '🔥 Лазерный', 'income': 25, 'slots': 3, 'price_metal': 2500},
    'quantum': {'name': '🌀 Квантовый', 'income': 70, 'slots': 4, 'price_metal': 10000},
    'ai': {'name': '🧠 ИИ-дрон', 'income': 200, 'slots': 5, 'price_metal': 50000}
}


@router.message(Command('drones'))
@router.message(F.text == '🚀 Ангар')
async def cmd_drones(message: Message):
    await show_drones_screen(message, message.from_user.id)


async def show_drones_screen(message_or_callback, user_id: int, edit: bool = False):
    from aiogram.types import Message
    user = await db.get_user(user_id)

    if not user:
        if isinstance(message_or_callback, Message):
            await message_or_callback.answer('Ошибка: пользователь не найден')
        return

    drone_count = 0
    max_drones = 50
    passive_income = 0

    text = (
        f'🚀 <b>ТВОЙ АНГАР</b>\n'
        f'Вместимость: {drone_count}/{max_drones}\n\n'
        f'📊 <b>ПАССИВНЫЙ ДОХОД:</b> +{passive_income}/5 сек\n\n'
    )

    if drone_count == 0:
        text += (
            '<i>У тебя пока нет дронов.</i>\n'
            'Дроны добывают ресурсы автоматически каждые 5 секунд, '
            'даже когда ты не в игре.\n\n'
            'Нажми «➕ Купить дрона», чтобы начать!'
        )
    else:
        text += '<i>Список дронов будет здесь...</i>'

    keyboard = [
        [
            InlineKeyboardButton(text='➕ Купить дрона', callback_data='buy_drone'),
            InlineKeyboardButton(text='🔧 Улучшить', callback_data='upgrade_drone'),
            InlineKeyboardButton(text='⚙️ Модули', callback_data='drone_modules')
        ],
        [
            InlineKeyboardButton(text='📊 Статистика', callback_data='drone_stats'),
            InlineKeyboardButton(text='🔄 Собрать доход', callback_data='collect_income'),
            InlineKeyboardButton(text='◀️ Назад', callback_data='back_to_menu')
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


@router.callback_query(F.data == 'buy_drone')
async def on_buy_drone(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    metal = user.get('metal', 0)
    crystals = user.get('crystals', 0)

    text = (
        f'🏪 <b>МАГАЗИН ДРОНОВ</b>\n\n'
        f'💰 Баланс: {metal:,} металла | {crystals:,} кристаллов\n\n'
    )

    keyboard = []

    for drone_key, drone in DRONE_TYPES.items():
        text += (
            f"<b>{drone['name']}</b>\n"
            f"▸ Доход: +{drone['income']}/5 сек\n"
            f"▸ Слотов модулей: {drone['slots']}\n"
            f"▸ Цена: {drone['price_metal']:,} металла\n\n"
        )
        keyboard.append([
            InlineKeyboardButton(
                text=f"Купить {drone['name'].split()[1]}",
                callback_data=f'purchase_drone_{drone_key}'
            )
        ])

    keyboard.append([
        InlineKeyboardButton(text='◀️ Назад', callback_data='back_to_hangar')
    ])

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data == 'back_to_hangar')
async def on_back_to_hangar(callback: CallbackQuery):
    await show_drones_screen(callback.message, callback.from_user.id, edit=True)
    await callback.answer()


@router.callback_query(F.data == 'back_to_menu')
async def on_back_to_menu(callback: CallbackQuery):
    from handlers.start import welcome_back_user
    user = await db.get_user(callback.from_user.id)
    await welcome_back_user(callback.message, user)
    await callback.answer()
