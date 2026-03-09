from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from database import db
from keyboards import (
    get_main_menu_keyboard,
    get_start_welcome_keyboard,
    get_start_return_keyboard
)

router = Router()


@router.message(Command('start'))
async def cmd_start(message: Message):
    user = await db.get_user(message.from_user.id)
    if user is None:
        await register_new_user(message)
    else:
        await welcome_back_user(message, user)


async def register_new_user(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    success = await db.create_user(user_id, username, first_name, last_name)

    if not success:
        await message.answer('Ошибка регистрации. Попробуйте позже.')
        return

    welcome_text = (
        '🚀 <b>ДОБРО ПОЖАЛОВАТЬ В ASTEROID MINER!</b>\n\n'
        'Шахтёр, ты находишься на орбите пояса астероидов Альфа-7.\n'
        'Твоя цель — добывать ресурсы, прокачивать дронов и открывать тайны галактики.\n\n'
        '✅ <b>Ты успешно зарегистрирован!</b>\n'
        f'Твой ID: <code>{user_id}</code>\n\n'
        '▸ Нажимай ⛏ Шахта, чтобы начать добычу\n'
        '▸ Покупай дронов для пассивного дохода\n'
        '▸ Собирай редкие артефакты\n'
        '▸ Торгуй с другими игроками\n'
        '▸ Объединяйся в кланы и круши боссов\n\n'
        '<b>Твой первый астероид уже ждёт тебя!</b>\n\n'
        '<b>Баланс:</b>\n'
        '▸ Металл: 0\n'
        '▸ Кристаллы: 0\n'
        '▸ Тёмная материя: 0\n'
        '▸ Энергия: 1000/1000'
    )

    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode='HTML'
    )

    await message.answer(
        'Куда отправимся?',
        reply_markup=get_start_welcome_keyboard()
    )


async def welcome_back_user(message: Message, user: dict):
    # Защита от None значений
    level = user.get("level") or 1
    total_mined = user.get("total_mined") or 0
    metal = user.get("metal") or 0
    crystals = user.get("crystals") or 0
    dark_matter = user.get("dark_matter") or 0
    energy = user.get("energy") or 0
    max_energy = user.get("max_energy") or 1000

    welcome_text = (
        '🚀 <b>С ВОЗВРАЩЕНИЕМ, ШАХТЁР!</b>\n\n'
        'Ты всё ещё в поясе астероидов. Продолжай добычу!\n\n'
        f'<b>Твой прогресс:</b>\n'
        f'▸ Уровень: {level}\n'
        f'▸ Дронов: 0/50\n'
        f'▸ Ресурсов всего: {total_mined:,}\n\n'
        f'<b>Баланс:</b>\n'
        f'▸ Металл: {metal:,}\n'
        f'▸ Кристаллы: {crystals:,}\n'
        f'▸ Тёмная материя: {dark_matter:,}\n'
        f'▸ Энергия: {energy}/{max_energy}\n\n'
        '<b>Куда отправимся?</b>'
    )

    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode='HTML'
    )

    await message.answer(
        'Выбери действие:',
        reply_markup=get_start_return_keyboard()
    )


@router.callback_query(F.data == 'start_game')
async def on_start_game(callback: CallbackQuery):
    await callback.answer('Переходим к добыче...')
    from handlers.mine import show_mine_screen
    await show_mine_screen(callback.message, callback.from_user.id, edit=True)


@router.callback_query(F.data == 'profile')
async def on_profile(callback: CallbackQuery):
    await callback.answer('Загружаем профиль...')
    await callback.message.answer('👤 Профиль')


@router.callback_query(F.data == 'top')
async def on_top(callback: CallbackQuery):
    await callback.answer('Загружаем топ...')
    await callback.message.answer('📊 Топ')


@router.callback_query(F.data == 'guide')
async def on_guide(callback: CallbackQuery):
    guide_text = (
        '📖 <b>БЫСТРЫЙ ГАЙД</b>\n\n'
        '<b>1. Добыча:</b> Жми ⛏ Добыть астероид для получения ресурсов\n'
        '<b>2. Энергия:</b> Тратится на каждый клик, восстанавливается со временем\n'
        '<b>3. Дроны:</b> Покупай в Ангаре для пассивного дохода\n'
        '<b>4. Прокачка:</b> Улучшай дроны, крафти модули\n'
        '<b>5. Торговля:</b> Продавай лишнее на Рынке\n\n'
        'Удачи, шахтёр! 🚀'
    )
    await callback.answer()
    await callback.message.answer(guide_text, parse_mode='HTML')


@router.callback_query(F.data == 'mine')
async def on_mine(callback: CallbackQuery):
    await callback.answer('Переходим...')
    from handlers.mine import show_mine_screen
    await show_mine_screen(callback.message, callback.from_user.id, edit=True)


@router.callback_query(F.data == 'drones')
async def on_drones(callback: CallbackQuery):
    await callback.answer('Открываем ангар...')
    from handlers.drones import show_drones_screen
    await show_drones_screen(callback.message, callback.from_user.id, edit=True)


@router.callback_query(F.data == 'inventory')
async def on_inventory(callback: CallbackQuery):
    await callback.answer('Открываем инвентарь...')
    from handlers.inventory import cmd_inventory
    await cmd_inventory(callback.message)


@router.callback_query(F.data == 'market')
async def on_market(callback: CallbackQuery):
    await callback.answer('Открываем рынок...')
    from handlers.market import cmd_market
    await cmd_market(callback.message)


@router.callback_query(F.data == 'craft')
async def on_craft(callback: CallbackQuery):
    await callback.answer('Открываем крафт...')
    from handlers.craft import cmd_craft
    await cmd_craft(callback.message)


@router.callback_query(F.data == 'clan')
async def on_clan(callback: CallbackQuery):
    await callback.answer('Открываем клан...')
    from handlers.clan import cmd_clan
    await cmd_clan(callback.message)
