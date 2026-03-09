from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import random
from database import db
from keyboards import get_mine_keyboard, get_buy_energy_keyboard

# Защита от накруток (8.2.2, 8.2.3)
from core import rate_limiter, click_protector, ActionType

# Игровые системы
from game import heat_system, LevelSystem

router = Router()
CLICK_ENERGY_COST = 10
BASE_MINE_AMOUNT = 10


@router.message(Command('mine'))
@router.message(F.text == '⛏ Шахта')
async def cmd_mine(message: Message):
    await show_mine_screen(message, message.from_user.id)


async def show_mine_screen(message_or_callback, user_id: int, edit: bool = False, level_up_info: dict = None):
    from aiogram.types import Message

    user = await db.get_user(user_id)
    if not user:
        if isinstance(message_or_callback, Message):
            await message_or_callback.answer('Ошибка: пользователь не найден')
        return

    # Получаем статистику
    stats = await db.get_user_stats(user_id)
    
    energy = user.get('energy', 1000)
    max_energy = user.get('max_energy', 1000)
    heat = user.get('heat', 0)
    level = user.get('level', 1)
    experience = user.get('experience', 0)
    
    # Расчёты
    energy_percent = int((energy / max_energy) * 100)
    energy_bar = '█' * (energy_percent // 10) + '░' * (10 - energy_percent // 10)

    heat_info = heat_system.get_heat_info(heat)
    heat_bar = heat_system.format_heat_bar(heat)
    
    level_info = LevelSystem.get_progress_info(level, experience)
    
    # Информация о дронах
    drones_count = stats.get('drones_count', 0)
    drones_income = stats.get('drones_income', 0)
    
    # Бонус от уровня
    mining_bonus = LevelSystem.get_mining_bonus(level)
    
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
        f'🤖 <b>АКТИВНЫЕ ДРОНЫ:</b> {drones_count} / 50\n'
        f'⏱ <b>ПАССИВНЫЙ ДОХОД:</b> +{drones_income:,}/5 сек\n\n'
        f'🌡 <b>ПЕРЕГРЕВ БУРОВ:</b> {heat}%\n'
        f'▸ {heat_bar}\n'
    )

    # Предупреждение о перегреве
    if heat_info.is_overheated:
        text += f'▸ 🔥 <b>ПЕРЕГРЕВ! Остывание {heat_info.cooldown_seconds} сек</b>\n'
    elif heat >= 80:
        text += f'▸ ⚡ Бонус добычи: x{heat_info.bonus_multiplier:.1f}\n'
    
    text += (
        f'\n📈 <b>УРОВЕНЬ: {level}</b> "{level_info["title"]}"\n'
        f'▸ Опыт: {experience:,} / {level_info["exp_needed"]:,} [{level_info["exp_bar"]}] {level_info["exp_percent"]}%\n'
        f'▸ Бонус добычи: +{int((mining_bonus - 1) * 100)}%\n\n'
        f'💥 <b>ШАНС КРИТА:</b> 3%\n'
        f'⭐ <b>ШАНС РЕДКОГО ЛУТА:</b> 5%\n\n'
        f'📦 <b>КОНТЕЙНЕРОВ ГОТОВО:</b> 0'
    )

    # Уведомление о повышении уровня
    if level_up_info and level_up_info.get('levels_gained', 0) > 0:
        new_level = level_up_info['new_level']
        new_title = LevelSystem.get_level_info(new_level).title
        energy_bonus = 50 * level_up_info['levels_gained']
        text += (
            f'\n\n🎉 <b>ПОЗДРАВЛЯЕМ!</b>\n'
            f'▸ Новый уровень: {new_level}\n'
            f'▸ Титул: "{new_title}"\n'
            f'▸ +{energy_bonus} макс. энергии'
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
    
    # Проверка перегрева
    user = await db.get_user(user_id)
    if not user:
        await callback.answer('Ошибка: пользователь не найден')
        return

    heat = user.get('heat', 0)
    heat_info = heat_system.get_heat_info(heat)
    
    if heat_info.is_overheated:
        await callback.answer(
            f'🔥 ПЕРЕГРЕВ! Буры остывают {heat_info.cooldown_seconds} сек',
            show_alert=True
        )
        return

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
    
    # Записываем клик в трекер
    click_interval = heat_system.record_click(user_id)
    
    # Записываем действие в лимитер
    await rate_limiter.record_action(user_id, ActionType.CLICK)

    current_energy = user.get('energy', 1000)

    if current_energy < CLICK_ENERGY_COST:
        await callback.answer(
            '❌ Недостаточно энергии! Купите энергию или подождите',
            show_alert=True
        )
        return

    # === РАСЧЁТ ДОБЫЧИ ===
    level = user.get('level', 1)
    
    # Базовая добыча
    base_mine = BASE_MINE_AMOUNT
    
    # Бонус от уровня
    level_bonus = LevelSystem.get_mining_bonus(level)
    
    # Бонус от перегрева
    heat_bonus = heat_info.bonus_multiplier
    
    # Итоговый множитель
    total_multiplier = level_bonus * heat_bonus
    
    # Крит-система
    crit_chance = 0.03
    is_crit = random.random() < crit_chance
    crit_multiplier = 1

    if is_crit:
        crit_roll = random.random()
        if crit_roll < 0.7:
            crit_multiplier = 2
            crit_text = '💥 КРИТ x2!'
        elif crit_roll < 0.9:
            crit_multiplier = 5
            crit_text = '🔥 МЕГА-КРИТ x5!'
        else:
            crit_multiplier = 10
            crit_text = '⚡ УЛЬТРА-КРИТ x10!'
        
        await callback.answer(crit_text, show_alert=False)
    else:
        # Обычный клик - тихое уведомление
        pass

    # Расчёт добычи
    final_multiplier = total_multiplier * crit_multiplier
    metal_gain = int(base_mine * final_multiplier * random.uniform(0.9, 1.1))
    crystal_gain = int(metal_gain * 0.1 * random.uniform(0.5, 1.5))
    dark_matter_gain = 1 if random.random() < 0.01 else 0
    
    # Опыт за клик
    exp_gain = LevelSystem.calculate_exp_reward("click", 1)
    
    # Расчёт перегрева
    heat_gain = heat_system.get_click_heat_increase(user_id, click_interval)
    
    # === ОБНОВЛЕНИЕ БД ===
    new_energy = current_energy - CLICK_ENERGY_COST
    
    # Обновляем ресурсы
    await db.update_user_resources(
        user_id,
        metal=metal_gain,
        crystals=crystal_gain,
        dark_matter=dark_matter_gain,
        energy=-CLICK_ENERGY_COST,
        total_clicks=1,
        total_mined=metal_gain + crystal_gain
    )

    # Добавляем опыт и проверяем уровень
    level_result = await db.add_experience(user_id, exp_gain)
    
    # Обновляем перегрев
    await db.update_heat(user_id, heat_gain)
    
    # Обновляем активность
    await db.update_last_activity(user_id)
    
    # Показываем экран с учётом повышения уровня
    level_up_info = level_result if level_result.get('levels_gained', 0) > 0 else None
    await show_mine_screen(callback.message, user_id, edit=True, level_up_info=level_up_info)


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
        energy=actual_amount
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
