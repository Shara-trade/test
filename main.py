"""
Точка входа для бота Asteroid Miner
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, BOT_COMMANDS
from database import db
from handlers import start, mine, drones, profile, top, help, admin
from handlers import inventory, market, craft, clan, galaxy, modules

# Core модули (8. Технические требования)
from core import cache, worker
from core.security import CallbackSecurityMiddleware, OwnershipMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def set_commands(bot: Bot):
    from aiogram.types import BotCommand
    commands = [BotCommand(command=cmd, description=desc) for cmd, desc in BOT_COMMANDS]
    await bot.set_my_commands(commands)


async def main():
    # Инициализация базы данных
    await db.init_db()
    logger.info('✅ База данных инициализирована')
    
    # Инициализация кэша (8.1.3)
    await cache.init()
    logger.info('✅ Кэш инициализирован')
    
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Подключение middleware безопасности (8.2.1)
    dp.callback_query.middleware(CallbackSecurityMiddleware())
    dp.callback_query.middleware(OwnershipMiddleware())
    logger.info('✅ Security middleware подключены')
    
    # Регистрация роутеров
    dp.include_router(start.router)
    dp.include_router(mine.router)
    dp.include_router(drones.router)
    dp.include_router(profile.router)
    dp.include_router(top.router)
    dp.include_router(help.router)
    dp.include_router(inventory.router)
    dp.include_router(modules.router)
    dp.include_router(market.router)
    dp.include_router(craft.router)
    dp.include_router(clan.router)
    dp.include_router(galaxy.router)
    dp.include_router(admin.router)
    
    await set_commands(bot)
    logger.info('✅ Команды бота установлены')
    
    # Запуск фонового воркера (8.1.4, 8.3.3)
    await worker.start()
    logger.info('✅ Background worker запущен')
    
    logger.info('🚀 Бот запущен!')
    
    try:
        await dp.start_polling(bot)
    finally:
        # Корректное завершение
        await worker.stop()
        logger.info('⏹ Background worker остановлен')


if __name__ == '__main__':
    asyncio.run(main())