"""
Конфигурация бота Asteroid Miner.
Все чувствительные данные загружаются из переменных окружения (.env файл).
"""
import os
import sys
from typing import List

# Загружаем переменные окружения из .env файла
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("WARNING: python-dotenv not installed. Using system environment variables.")
    print("Install with: pip install python-dotenv")


def get_env_int(key: str, default: int = 0) -> int:
    """Получить целое число из переменной окружения"""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        print(f"WARNING: Invalid integer value for {key}, using default: {default}")
        return default


def get_env_list(key: str, default: List[int] = None) -> List[int]:
    """Получить список целых чисел из переменной окружения (через запятую)"""
    value = os.getenv(key)
    if value is None:
        return default or []
    try:
        return [int(x.strip()) for x in value.split(",") if x.strip()]
    except ValueError:
        print(f"WARNING: Invalid list value for {key}, using default")
        return default or []


# ===== ОБЯЗАТЕЛЬНЫЕ ПЕРЕМЕННЫЕ =====

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN is not set!")
    print("Create .env file with BOT_TOKEN=your_token")
    sys.exit(1)

DATABASE_PATH = os.getenv("DATABASE_PATH", "asteroid_miner.db")

ADMIN_IDS = get_env_list("ADMIN_IDS")
if not ADMIN_IDS:
    print("WARNING: ADMIN_IDS is not set. Admin panel will be inaccessible.")

# ===== ИГРОВЫЕ КОНСТАНТЫ =====

START_ENERGY = 1000
MAX_ENERGY_BASE = 1000
CLICK_ENERGY_COST = 10
BASE_MINE_AMOUNT = 10

# ===== КОМАНДЫ БОТА =====

BOT_COMMANDS = [
    ("start", "Перезапуск / приветствие"),
    ("mine", "Главная шахта (добыча)"),
    ("angar", "Ангар с дронами"),
    ("drones", "Ангар с дронами"),
    ("inventory", "Инвентарь"),
    ("market", "Рынок игроков"),
    ("craft", "Крафт-станция"),
    ("clan", "Моя корпорация"),
    ("galaxy", "Карта галактики"),
    ("profile", "Мой профиль"),
    ("top", "Топ игроков"),
    ("help", "Помощь / FAQ"),
    ("admin", "Админ-панель"),
]

# ===== ЛОГИРОВАНИЕ =====

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ===== REDIS (ОПЦИОНАЛЬНО) =====

REDIS_URL = os.getenv("REDIS_URL", "")
