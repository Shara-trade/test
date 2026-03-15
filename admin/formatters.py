"""
Утилиты для форматирования данных в админ-панели
"""
from typing import Dict, List, Optional
from datetime import datetime


def format_number(n: int) -> str:
    """Форматирование числа с разделителями"""
    return f"{n:,}".replace(",", " ")


def format_datetime(dt_str: Optional[str]) -> str:
    """Форматирование даты и времени"""
    if not dt_str:
        return "N/A"
    
    try:
        # Парсим ISO формат
        if "T" in dt_str:
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            return dt.strftime("%d.%m.%Y %H:%M")
        # Парсим простой формат
        return dt_str[:16] if len(dt_str) >= 16 else dt_str
    except:
        return dt_str


def format_date(dt_str: Optional[str]) -> str:
    """Форматирование только даты"""
    if not dt_str:
        return "N/A"
    
    try:
        if "T" in dt_str:
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            return dt.strftime("%d.%m.%Y")
        return dt_str[:10] if len(dt_str) >= 10 else dt_str
    except:
        return dt_str


def format_duration(seconds: int) -> str:
    """Форматирование длительности"""
    if seconds < 60:
        return f"{seconds} сек."
    elif seconds < 3600:
        return f"{seconds // 60} мин."
    elif seconds < 86400:
        return f"{seconds // 3600} ч."
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days} д. {hours} ч."


# ==================== ФОРМАТИРОВАНИЕ ИГРОКА ====================

def format_player_card(player: Dict) -> str:
    """
    Форматирование карточки игрока для админки.
    
    Args:
        player: Dict с данными игрока
        
    Returns:
        str - отформатированный текст
    """
    user_id = player.get("user_id", "N/A")
    username = player.get("username") or player.get("first_name") or "Неизвестно"
    
    status = "🚫 Забанен" if player.get("is_banned") else "🟢 Активен"
    
    text = (
        f"👤 <b>КАРТОЧКА ИГРОКА</b>\n\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"📝 Username: @{username}\n"
        f"📅 Регистрация: {format_date(player.get('created_at'))}\n"
        f"🕐 Последняя активность: {format_datetime(player.get('last_activity'))}\n\n"
        f"📊 <b>ПРОГРЕСС:</b>\n"
        f"▸ Уровень: {player.get('level', 1)}\n"
        f"▸ Престиж: {player.get('prestige', 0)}\n"
        f"▸ Опыт: {format_number(player.get('experience', 0))}\n\n"
        f"💰 <b>РЕСУРСЫ:</b>\n"
        f"▸ ⚙️ Металл: {format_number(player.get('metal', 0))}\n"
        f"▸ 💎 Кристаллы: {format_number(player.get('crystals', 0))}\n"
        f"▸ 🕳️ Тёмная материя: {format_number(player.get('dark_matter', 0))}\n"
        f"▸ 💵 Кредиты: {format_number(player.get('credits', 0))}\n"
        f"▸ 🎫 Квант-токены: {player.get('quantum_tokens', 0)}\n\n"
        f"📦 <b>ИНВЕНТАРЬ:</b>\n"
        f"▸ Контейнеры: {player.get('containers_count', 0)}\n"
        f"▸ Модули: {player.get('modules_count', 0)}\n"
        f"▸ Материалы: {format_number(player.get('materials_count', 0))}\n"
        f"▸ Дроны: {player.get('drones_count', 0)}\n\n"
        f"📈 <b>СТАТИСТИКА:</b>\n"
        f"▸ Всего кликов: {format_number(player.get('total_clicks', 0))}\n"
        f"▸ Добыто всего: {format_number(player.get('total_mined', 0))}\n"
        f"▸ Статус: {status}"
    )
    
    return text


def format_player_short(player: Dict) -> str:
    """
    Краткое форматирование игрока для списка.
    
    Args:
        player: Dict с данными игрока
        
    Returns:
        str - отформатированная строка
    """
    user_id = player.get("user_id", "N/A")
    username = player.get("username") or player.get("first_name") or "N/A"
    level = player.get("level", 1)
    status = "🚫" if player.get("is_banned") else "🟢"
    
    return f"{status}<code>{user_id}</code> @{username} (Lvl.{level})"


# ==================== ФОРМАТИРОВАНИЕ ИСТОРИИ ====================

ACTION_EMOJIS = {
    "edit_resource": "✏️",
    "give_item": "📦",
    "give_container": "📦",
    "give_module": "🧩",
    "give_material": "🧱",
    "ban_player": "🚫",
    "unban_player": "✅",
    "reset_player": "♻️",
    "apply_preset": "🎁",
    "mass_operation": "👥",
    "edit_setting": "⚙️",
    "admin_action": "🔧",
}

ACTION_NAMES = {
    "edit_resource": "Изменение ресурсов",
    "give_item": "Выдача предмета",
    "give_container": "Выдача контейнера",
    "give_module": "Выдача модуля",
    "give_material": "Выдача материала",
    "ban_player": "Бан игрока",
    "unban_player": "Разбан игрока",
    "reset_player": "Сброс игрока",
    "apply_preset": "Применение пресета",
    "mass_operation": "Массовая операция",
    "edit_setting": "Изменение настройки",
    "admin_action": "Действие админа",
}


def format_history_event(event: Dict) -> str:
    """
    Форматирование одного события истории.
    
    Args:
        event: Dict с данными события
        
    Returns:
        str - отформатированная строка
    """
    time = format_datetime(event.get("created_at"))
    action = event.get("action", "unknown")
    details = event.get("details", "")
    admin_name = event.get("admin_name", "N/A")
    
    emoji = ACTION_EMOJIS.get(action, "📌")
    action_name = ACTION_NAMES.get(action, action)
    
    return f"{time} {emoji} {action_name}\n   └ {details} (by @{admin_name})"


def format_player_history(events: List[Dict], user_id: int) -> str:
    """
    Форматирование истории игрока.
    
    Args:
        events: List событий
        user_id: ID игрока
        
    Returns:
        str - отформатированный текст
    """
    text = f"📜 <b>ИСТОРИЯ ИГРОКА</b>\n"
    text += f"ID: <code>{user_id}</code>\n\n"
    
    if not events:
        text += "📭 История пуста"
        return text
    
    for event in events[:20]:  # Максимум 20 событий
        text += format_history_event(event) + "\n\n"
    
    return text


# ==================== ФОРМАТИРОВАНИЕ ЛОГОВ ====================

def format_log_entry(log: Dict) -> str:
    """
    Форматирование записи лога.
    
    Args:
        log: Dict с данными лога
        
    Returns:
        str - отформатированная строка
    """
    time = format_datetime(log.get("created_at"))
    admin_name = log.get("admin_username", "N/A")
    action = log.get("action", "unknown")
    target = log.get("target_user_id")
    details = log.get("details", "")
    
    emoji = ACTION_EMOJIS.get(action, "📌")
    action_name = ACTION_NAMES.get(action, action)
    
    target_str = f" → <code>{target}</code>" if target else ""
    
    return f"{time} | @{admin_name} {emoji} {action_name}{target_str}\n   └ {details}"


def format_admin_logs(logs: List[Dict], page: int = 1) -> str:
    """
    Форматирование списка логов.
    
    Args:
        logs: List логов
        page: Номер страницы
        
    Returns:
        str - отформатированный текст
    """
    text = f"📜 <b>ЛОГИ АДМИНОВ</b>\n"
    text += f"Страница: {page}\n\n"
    
    if not logs:
        text += "📭 Логи пусты"
        return text
    
    for log in logs:
        text += format_log_entry(log) + "\n\n"
    
    return text


# ==================== ФОРМАТИРОВАНИЕ СТАТИСТИКИ ====================

def format_admin_stats(stats: Dict) -> str:
    """
    Форматирование статистики для админки.
    
    Args:
        stats: Dict со статистикой
        
    Returns:
        str - отформатированный текст
    """
    text = "📊 <b>СТАТИСТИКА БОТА</b>\n\n"
    
    text += "👥 <b>ИГРОКИ:</b>\n"
    text += f"▸ Всего игроков: {format_number(stats.get('total_players', 0))}\n"
    text += f"▸ Активных сегодня: {format_number(stats.get('active_today', 0))}\n"
    text += f"▸ Онлайн сейчас: {stats.get('online_now', 0)}\n"
    text += f"▸ Забаненных: {stats.get('banned_players', 0)}\n\n"
    
    text += "📈 <b>РЕГИСТРАЦИИ:</b>\n"
    text += f"▸ Новых сегодня: {stats.get('new_players_today', 0)}\n"
    text += f"▸ Новых за неделю: {stats.get('new_players_week', 0)}\n\n"
    
    text += "💰 <b>ЭКОНОМИКА:</b>\n"
    text += f"▸ Всего металла: {format_number(stats.get('total_metal', 0))}\n"
    text += f"▸ Всего кристаллов: {format_number(stats.get('total_crystals', 0))}\n"
    text += f"▸ Всего кредитов: {format_number(stats.get('total_credits', 0))}\n"
    
    return text


def format_realtime_stats(stats: Dict) -> str:
    """
    Форматирование статистики в реальном времени.
    
    Args:
        stats: Dict со статистикой
        
    Returns:
        str - отформатированный текст
    """
    text = "📊 <b>СТАТИСТИКА В РЕАЛЬНОМ ВРЕМЕНИ</b>\n\n"
    
    text += f"🟢 Онлайн сейчас: {stats.get('online_now', 0)}\n"
    text += f"👥 Активных за час: {stats.get('active_hour', 0)}\n"
    text += f"⛏️ Добыто за час: {format_number(stats.get('mined_hour', 0))}\n\n"
    
    text += f"🕐 Обновлено: {format_datetime(stats.get('timestamp'))}"
    
    return text


# ==================== ФОРМАТИРОВАНИЕ ПРЕСЕТОВ ====================

def format_preset(preset: Dict) -> str:
    """
    Форматирование описания пресета.
    
    Args:
        preset: Dict с данными пресета
        
    Returns:
        str - отформатированный текст
    """
    text = f"{preset.get('name', 'Пресет')}\n\n"
    
    items = preset.get("items", [])
    if items:
        text += "📦 <b>Предметы:</b>\n"
        for item_key, qty in items:
            text += f"  • {item_key} x{qty}\n"
        text += "\n"
    
    resources = preset.get("resources", {})
    if resources:
        text += "💰 <b>Ресурсы:</b>\n"
        if resources.get("metal"):
            text += f"  • Металл: {format_number(resources['metal'])}\n"
        if resources.get("crystals"):
            text += f"  • Кристаллы: {format_number(resources['crystals'])}\n"
        if resources.get("dark_matter"):
            text += f"  • Тёмная материя: {format_number(resources['dark_matter'])}\n"
    
    return text


def format_presets_list(presets: List[Dict]) -> str:
    """
    Форматирование списка пресетов.
    
    Args:
        presets: List пресетов
        
    Returns:
        str - отформатированный текст
    """
    text = "🎁 <b>ШАБЛОНЫ ДЕЙСТВИЙ</b>\n\n"
    
    if not presets:
        text += "📭 Нет доступных пресетов"
        return text
    
    for i, preset in enumerate(presets, 1):
        text += f"{i}. {preset.get('name', preset.get('id'))}\n"
        text += f"   ID: <code>{preset.get('id')}</code>\n\n"
    
    return text


# ==================== ВСПОМОГАТЕЛЬНЫЕ ====================

def get_timestamp() -> str:
    """Получить текущее время"""
    return datetime.now().strftime("%d.%m.%Y %H:%M")
