from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import random
from database import db
from keyboards import get_mine_keyboard, get_buy_energy_keyboard

# Защита от накруток (8.2.2, 8.2.3)
from core import rate_limiter, click_protector, ActionType

# Игровые системы
from game import heat_system, LevelSystem, asteroid_system, loot_system, container_system

router = Router()
CLICK_ENERGY_COST = 10


@router.message(Command('mine'))
@router.message(F.text == '⛏ Шахта')
async def cmd_mine(message: Message):
    await show_mine_screen(message, message.from_user.id)


async def show_mine_screen(message_or_callback, user_id: int, edit: bool = False, level_up_info: dict = None):
    from aiogram.types import Message
    import logging
    logger = logging.getLogger("mine")

    user = await db.get_user(user_id)
    if not user:
        if isinstance(message_or_callback, Message):
            await message_or_callback.answer('Ошибка: пользователь не найден')
        return

    # Логируем загруженные данные
    logger.info(f"show_mine_screen: user={user_id}, level={user.get('level')}, exp={user.get('experience')}")

    # Получаем статистику
    stats = await db.get_user_stats(user_id)
    
    # Безопасное получение значений (защита от NULL в БД)
    energy = user.get('energy') or 1000
    max_energy = user.get('max_energy') or 1000
    heat = user.get('heat') or 0
    level = user.get('level') or 1
    experience = user.get('experience') or 0
    metal = user.get('metal') or 0
    crystals = user.get('crystals') or 0
    dark_matter = user.get('dark_matter') or 0
    
    # Убедимся что это числа
    level = int(level) if level else 1
    experience = int(experience) if experience else 0
    
    # Расчёты
    energy_percent = int((energy / max_energy) * 100) if max_energy > 0 else 0
    energy_bar = '█' * (energy_percent // 10) + '░' * (10 - energy_percent // 10)

    heat_info = heat_system.get_heat_info(heat)
    heat_bar = heat_system.format_heat_bar(heat)
    
    level_info = LevelSystem.get_progress_info(level, experience)
    
    # Информация о дронах
    drones_count = stats.get('drones_count') or 0
    drones_income = stats.get('drones_income') or 0
    
    # Контейнеры
    containers_count = await db.get_containers_count(user_id)
    
    # Проверяем блокировку перегрева
    block_status = await db.get_heat_block_status(user_id)
    is_heat_blocked = block_status.get("is_blocked", False)
    block_remaining = block_status.get("remaining_seconds", 0)
    
    # Бонус от уровня
    mining_bonus = LevelSystem.get_mining_bonus(level)
    
    text = (
        f'⛏ <b>АСТЕРОИДНЫЙ ПОЯС АЛЬФА-7</b>\n'
        f'Система: Солнечная\n'
        f'Активность: Высокая\n\n'
        f'📊 <b>РЕСУРСЫ В ТРЮМЕ:</b>\n'
        f'▸ Металл: {metal:,} ⚙️\n'
        f'▸ Кристаллы: {crystals:,} 💎\n'
        f'▸ Тёмная материя: {dark_matter:,} ⚫\n\n'
        f'⚡ <b>ЭНЕРГИЯ БУРОВ:</b>\n'
        f'▸ {energy:,} / {max_energy:,} ⚡ [{energy_bar}] {energy_percent}%\n\n'
        f'🤖 <b>АКТИВНЫЕ ДРОНЫ:</b> {drones_count} / 50\n'
        f'⏱ <b>ПАССИВНЫЙ ДОХОД:</b> +{drones_income:,}/5 сек\n\n'
        f'🌡 <b>ПЕРЕГРЕВ БУРОВ:</b> {heat}%\n'
        f'▸ {heat_bar}\n'
    )

    # Предупреждение о перегреве
    if is_heat_blocked:
        text += f'▸ 🔥 <b>ПЕРЕГРЕВ! Блокировка {block_remaining} сек</b>\n'
    elif heat_info.is_overheated:
        text += f'▸ 🔥 <b>ПЕРЕГРЕВ! Блокировка 60 сек</b>\n'
    elif heat >= 80:
        text += f'▸ ⚡ Бонус добычи: x{heat_info.bonus_multiplier:.1f}\n'
    
    text += (
        f'\n📈 <b>УРОВЕНЬ: {level}</b> "{level_info["title"]}"\n'
        f'▸ Опыт: {experience:,} / {level_info["exp_needed"]:,} [{level_info["exp_bar"]}] {level_info["exp_percent"]}%\n'
        f'▸ Бонус добычи: +{int((mining_bonus - 1) * 100)}%\n\n'
        f'💥 <b>ШАНС КРИТА:</b> 3%\n'
        f'⭐ <b>ШАНС РЕДКОГО ЛУТА:</b> 5%\n\n'
        f'📦 <b>КОНТЕЙНЕРОВ:</b> {containers_count} / 10'
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
    try:
        user_id = callback.from_user.id
        
        # Получаем СВЕЖИЕ данные пользователя из БД
        user = await db.get_user(user_id)
        if not user:
            await callback.answer('Ошибка: пользователь не найден')
            return

        # Проверка блокировки перегрева
        block_status = await db.get_heat_block_status(user_id)
        
        if block_status.get("is_blocked"):
            remaining = block_status.get("remaining_seconds", 60)
            await callback.answer(
                f'🔥 ПЕРЕГРЕВ! Буры остывают {remaining} сек',
                show_alert=True
            )
            return

        # Проверка перегрева
        heat = user.get('heat') or 0
        
        if heat >= 100:
            # Устанавливаем блокировку на 60 секунд
            await db.set_heat_block(user_id, 60)
            await callback.answer(
                '🔥 ПЕРЕГРЕВ! Буры заблокированы на 60 сек',
                show_alert=True
            )
            await show_mine_screen(callback.message, user_id, edit=True)
            return

        heat_info = heat_system.get_heat_info(heat)

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

        current_energy = user.get('energy') or 1000

        if current_energy < CLICK_ENERGY_COST:
            await callback.answer(
                '❌ Недостаточно энергии! Купите энергию или подождите',
                show_alert=True
            )
            return

        # === ГЕНЕРАЦИЯ АСТЕРОИДА ===
        asteroid = asteroid_system.generate_asteroid()
        
        # === РАСЧЁТ БОНУСОВ ===
        level = user.get('level') or 1
        level_bonus = LevelSystem.get_mining_bonus(level)
        heat_bonus = heat_info.bonus_multiplier
        
        # === КРИТ-СИСТЕМА ===
        crit_chance = 0.03  # 3% базовый шанс
        is_crit = random.random() < crit_chance
        crit_multiplier = 1
        crit_text = ""

        if is_crit:
            crit_roll = random.random()
            if crit_roll < 0.7:
                crit_multiplier = 2
                crit_text = "💥 КРИТ x2!"
            elif crit_roll < 0.9:
                crit_multiplier = 5
                crit_text = "🔥 МЕГА-КРИТ x5!"
            else:
                crit_multiplier = 10
                crit_text = "⚡ УЛЬТРА-КРИТ x10!"

        # === РАСЧЁТ НАГРАД ===
        total_bonus = level_bonus * heat_bonus
        rewards = asteroid_system.get_asteroid_rewards(asteroid, total_bonus)
        
        metal_gain = rewards["metal"] * crit_multiplier
        crystal_gain = rewards["crystals"] * crit_multiplier
        dark_matter_gain = rewards["dark_matter"] * crit_multiplier
        
        # Опыт: базовый от астероида * крит-множитель
        exp_gain = rewards["exp_reward"] * crit_multiplier
        
        # Перегрев
        heat_gain = heat_system.get_click_heat_increase(user_id, click_interval)
        
        # === ПРОВЕРКА ЛУТА ===
        loot_item = loot_system.try_drop()
        loot_text = ""
        
        if loot_item:
            loot_text = f"\n{loot_system.format_loot_message(loot_item)}"
            # Добавляем предмет в инвентарь
            await db.add_inventory_item(user_id, loot_item.key, 1)
        
        # === ПРОВЕРКА КОНТЕЙНЕРА ===
        container_info = container_system.try_drop_container()
        container_text = ""
        
        if container_info:
            # Проверяем лимит контейнеров
            containers_count = await db.get_containers_count(user_id)
            if container_system.can_receive_container(containers_count):
                container_text = f"\n{container_system.format_container_drop(container_info)}"
                # Добавляем контейнер
                await db.add_container(user_id, container_info.container_type.value)
        
        # === ФОРМИРОВАНИЕ СООБЩЕНИЯ ===
        result_lines = []
        
        # Тип астероида
        if is_crit:
            result_lines.append(f"{crit_text} {asteroid.emoji} {asteroid.name}!")
        else:
            result_lines.append(f"{asteroid.emoji} {asteroid.name}!")
        
        # Ресурсы
        resource_parts = []
        if metal_gain > 0:
            resource_parts.append(f"+{metal_gain:,} ⚙️")
        if crystal_gain > 0:
            resource_parts.append(f"+{crystal_gain:,} 💎")
        if dark_matter_gain > 0:
            resource_parts.append(f"+{dark_matter_gain:,} ⚫")
        
        if resource_parts:
            result_lines.append(" | ".join(resource_parts))
        
        # Опыт
        if exp_gain > 1:
            result_lines.append(f"✨ +{exp_gain} опыта")
        
        # Бонус от перегрева
        if heat_bonus > 1.0:
            result_lines.append(f"⚡ Бонус: x{heat_bonus:.1f}")
        
        # Лут и контейнер
        if loot_text:
            result_lines.append(loot_text.strip())
        if container_text:
            result_lines.append(container_text.strip())
        
        popup_text = "\n".join(result_lines)
        
        # Ограничиваем длину popup (Telegram limit ~200 chars)
        if len(popup_text) > 200:
            popup_text = popup_text[:197] + "..."
        
        # === ОБНОВЛЕНИЕ БД ===
        await db.update_user_resources(
            user_id,
            metal=metal_gain,
            crystals=crystal_gain,
            dark_matter=dark_matter_gain,
            energy=-CLICK_ENERGY_COST,
            total_clicks=1,
            total_mined=metal_gain + crystal_gain
        )

        # Добавляем опыт
        import logging
        logger = logging.getLogger("mine")
        logger.info(f"Adding {exp_gain} exp to user {user_id}")
        
        level_result = await db.add_experience(user_id, exp_gain)
        logger.info(f"add_experience result: {level_result}")
        
        if not level_result.get("success"):
            logger.error(f"Failed to add experience: {level_result.get('error')}")
        
        # Обновляем перегрев и проверяем блокировку
        heat_result = await db.update_heat(user_id, heat_gain)
        
        # Если перегрев достиг 100% - устанавливаем блокировку на 60 секунд
        if heat_result.get("is_overheated"):
            await db.set_heat_block(user_id, 60)
            
            # Показываем результат + уведомление о блокировке
            try:
                await callback.answer(
                    f"{popup_text}\n🔥 ПЕРЕГРЕВ 100%!\nБлокировка 60 сек",
                    show_alert=False
                )
            except:
                await callback.answer("🔥 ПЕРЕГРЕВ 100%! Блокировка 60 сек", show_alert=False)
            
            # Обновляем экран
            level_up_info = level_result if level_result.get('levels_gained', 0) > 0 else None
            await show_mine_screen(callback.message, user_id, edit=True, level_up_info=level_up_info)
            return
        
        # Обновляем активность
        await db.update_last_activity(user_id)
        
        # Показываем результат
        try:
            await callback.answer(popup_text, show_alert=False)
        except Exception as e:
            # Если текст слишком длинный, показываем короткий
            await callback.answer(f"{asteroid.emoji} {asteroid.name}!", show_alert=False)
        
        # Обновляем экран
        level_up_info = level_result if level_result.get('levels_gained', 0) > 0 else None
        await show_mine_screen(callback.message, user_id, edit=True, level_up_info=level_up_info)
        
    except Exception as e:
        import logging
        logging.error(f"Mine click error: {e}")
        await callback.answer(f"Ошибка: {str(e)[:50]}", show_alert=True)


@router.callback_query(F.data == 'refresh_mine')
async def on_refresh_mine(callback: CallbackQuery):
    await callback.answer('Обновляем...')
    await show_mine_screen(callback.message, callback.from_user.id, edit=True)


@router.callback_query(F.data == 'buy_energy')
async def on_buy_energy(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    metal = user.get('metal') or 0

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
    current_metal = user.get('metal') or 0
    current_energy = user.get('energy') or 0
    max_energy = user.get('max_energy') or 1000

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
