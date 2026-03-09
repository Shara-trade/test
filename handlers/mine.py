from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import random
from database import db
from keyboards import get_mine_keyboard, get_buy_energy_keyboard

# Защита от накруток (8.2.2, 8.2.3)
from core import rate_limiter, click_protector, ActionType

router = Router()
CLICK_ENERGY_COST = 10
BASE_MINE_AMOUNT = 10


@router.message(Command('mine'))
@router.message(F.text == '⛏ Шахта')
async def cmd_mine(message: Message):
    await show_mine_screen(message, message.from_user.id)


async def show_mine_screen(message_or_callback, user_id: int, edit: bool = False):
    from aiogram.types import Message

    user = await db.get_user(user_id)
    if not user:
        if isinstance(message_or_callback, Message):
            await message_or_callback.answer('Ошибка: пользователь не найден')
        return

    energy = user.get('energy', 1000)
    max_energy = user.get('max_energy', 1000)
    energy_percent = int((energy / max_energy) * 100)
    energy_bar = '█' * (energy_percent // 10) + '░' * (10 - energy_percent // 10)

    text = (
        f'⛏ <b>АСТЕРОИДНЫЙ ПОЯС АЛЬФА-7</b>\n'
        f'Система: Солнечная\n'
        f'Активность: Высокая\n\n'
        f'📊 <b>РЕСУРСЫ В ТРЮМЕ:</b>\n'
        f'▸ Металл: {user.get("metal", 0):,} ⚙️\n'
        f'▸ Кристаллы: {user.get("crystals", 0):,} 💎\n'
        f'▸ Тёмная материя: {user.get("dark_matter", 0):,} ⚫\n\n'
        f'⚡ <b>ЭНЕРГИЯ БУРОВ:</b>\n'
        f'▸ {energy:,} / {max_energy:,} ⚡ [{energy_bar}] {energy_percent}%\n\n'
        f'🤖 <b>АКТИВНЫЕ ДРОНЫ:</b> 0 / 50\n'
        f'⏱ <b>ПАССИВНЫЙ ДОХОД:</b> +0/5 сек\n\n'
        f'🌡 <b>ПЕРЕГРЕВ БУРОВ:</b> 0%\n\n'
        f'💥 <b>ШАНС КРИТА:</b> 3%\n'
        f'⭐ <b>ШАНС РЕДКОГО ЛУТА:</b> 5%\n\n'
        f'📦 <b>КОНТЕЙНЕРОВ ГОТОВО:</b> 0'
    )

    if edit and isinstance(message_or_callback, Message):
        try:
            await message_or_callback.edit_text(
                text,
                reply_markup=get_mine_keyboard(),
                parse_mode='HTML'
            )
        except:
            await message_or_callback.answer(
                text,
                reply_markup=get_mine_keyboard(),
                parse_mode='HTML'
            )
    else:
        await message_or_callback.answer(
            text,
            reply_markup=get_mine_keyboard(),
            parse_mode='HTML'
        )


@router.callback_query(F.data == 'mine_click')
async def on_mine_click(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    # 8.2.2 Защита от быстрых кликов
    allowed, status, speed = await click_protector.check_click(user_id)
    
    if not allowed:
        if status == "blocked":
            remaining = int(speed) if speed else 60
            await callback.answer(
                f'🚫 Подозрительная активность! Блокировка на {remaining} сек',
                show_alert=True
            )
        return

    # 8.2.3 Проверка лимита кликов
    allowed, error_msg = await rate_limiter.check_action(user_id, ActionType.CLICK)
    
    if not allowed:
        await callback.answer(error_msg, show_alert=True)
        return

    # Записываем действие
    await rate_limiter.record_action(user_id, ActionType.CLICK)
    
    user = await db.get_user(user_id)

    if not user:
        await callback.answer('Ошибка: пользователь не найден')
        return

    current_energy = user.get('energy', 1000)

    if current_energy < CLICK_ENERGY_COST:
        await callback.answer(
            '❌ Недостаточно энергии! Купите энергию или подождите',
            show_alert=True
        )
        return

    base_mine = BASE_MINE_AMOUNT

    # Крит-система
    crit_chance = 0.03
    is_crit = random.random() < crit_chance
    crit_multiplier = 1

    if is_crit:
        crit_roll = random.random()
        if crit_roll < 0.7:
            crit_multiplier = 2
            await callback.answer('💥 КРИТ x2!', show_alert=False)
        elif crit_roll < 0.9:
            crit_multiplier = 5
            await callback.answer('🔥 МЕГА-КРИТ x5!', show_alert=False)
        else:
            crit_multiplier = 10
            await callback.answer('⚡ УЛЬТРА-КРИТ x10!', show_alert=False)

    metal_gain = int(base_mine * crit_multiplier * random.uniform(0.9, 1.1))
    crystal_gain = int(metal_gain * 0.1 * random.uniform(0.5, 1.5))
    dark_matter_gain = 1 if random.random() < 0.01 else 0

    new_energy = current_energy - CLICK_ENERGY_COST

    await db.update_user_resources(
        user_id,
        metal=metal_gain,
        crystals=crystal_gain,
        dark_matter=dark_matter_gain,
        energy=new_energy
    )

    await show_mine_screen(callback.message, user_id, edit=True)


@router.callback_query(F.data == 'refresh_mine')
async def on_refresh_mine(callback: CallbackQuery):
    await callback.answer('Обновляем...')
    await show_mine_screen(callback.message, callback.from_user.id, edit=True)


@router.callback_query(F.data == 'buy_energy')
async def on_buy_energy(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    metal = user.get('metal', 0)

    text = (
        f'⚡ <b>ВОСПОЛНИТЬ ЭНЕРГИЮ</b>\n\n'
        f'💰 Баланс металла: {metal:,}\n\n'
        f'▸ 100 энергии — 50 металла\n'
        f'▸ 500 энергии — 200 металла\n'
        f'▸ 1000 энергии — 350 металла'
    )

    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_buy_energy_keyboard(),
            parse_mode='HTML'
        )
    except:
        await callback.message.answer(
            text,
            reply_markup=get_buy_energy_keyboard(),
            parse_mode='HTML'
        )
    await callback.answer()


@router.callback_query(F.data.startswith('buy_energy_'))
async def on_buy_energy_amount(callback: CallbackQuery):
    amount = int(callback.data.split('_')[-1])
    prices = {100: 50, 500: 200, 1000: 350}
    price = prices.get(amount, 50)

    user = await db.get_user(callback.from_user.id)
    current_metal = user.get('metal', 0)
    current_energy = user.get('energy', 1000)
    max_energy = user.get('max_energy', 1000)

    if current_metal < price:
        await callback.answer('Недостаточно металла!', show_alert=True)
        return

    if current_energy >= max_energy:
        await callback.answer('Энергия уже полная!', show_alert=True)
        return

    new_energy = min(current_energy + amount, max_energy)
    actual_amount = new_energy - current_energy

    await db.update_user_resources(
        callback.from_user.id,
        metal=-price,
        energy=new_energy
    )

    await callback.answer(f'Куплено {actual_amount} энергии!')
    await show_mine_screen(callback.message, callback.from_user.id, edit=True)


@router.callback_query(F.data == 'back_to_mine')
async def on_back_to_mine(callback: CallbackQuery):
    await show_mine_screen(callback.message, callback.from_user.id, edit=True)
    await callback.answer()


@router.callback_query(F.data == 'main_menu')
async def on_main_menu(callback: CallbackQuery):
    from handlers.start import welcome_back_user
    user = await db.get_user(callback.from_user.id)
    await welcome_back_user(callback.message, user)
    await callback.answer()
