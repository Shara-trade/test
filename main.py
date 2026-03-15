import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, BOT_COMMANDS
from database import db
from database.migrations import MigrationManager
from database.pool import init_pool, close_pool
from handlers import start, mine, drones, profile, top, help
from handlers import inventory, market, craft, clan, galaxy, modules
from handlers.admin_panel import router as admin_router

# Core модули (8. Технические требования)   
from core import cache, worker
from core.security import CallbackSecurityMiddleware, OwnershipMiddleware

# Admin middleware (пункт 2 ТЗ)
from admin import get_rate_limit_middleware, get_audit_middleware
from config import DATABASE_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def set_commands(bot: Bot):
    from aiogram.types import BotCommand
    commands = [BotCommand(command=cmd, description=desc) for cmd, desc in BOT_COMMANDS]
    await bot.set_my_commands(commands)


async def main():
    # Инициализация connection pool
    await init_pool()
    logger.info('✅ Connection pool инициализирован')
    
    # Инициализация базы данных
    await db.init_db()
    logger.info('✅ База данных инициализирована')
    
    # Применение миграций
    migration_manager = MigrationManager(db.db_path)
    pending = migration_manager.get_pending_migrations()
    if pending:
        applied = await migration_manager.apply_all_pending()
        logger.info(f'✅ Применено миграций: {applied}/{len(pending)}')
    else:
        logger.info('✅ Миграции актуальны')
    
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
    
    # Подключение admin middleware (пункт 2 ТЗ)
    rate_limit_mw = get_rate_limit_middleware()
    audit_mw = get_audit_middleware(DATABASE_PATH)
    dp.callback_query.middleware(rate_limit_mw)
    dp.callback_query.middleware(audit_mw)
    logger.info('✅ Admin middleware подключены (Rate Limit + Audit)')
    
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
    dp.include_router(admin_router)
    
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

        # Закрытие connection pool
        await close_pool()
        logger.info('⏹ Connection pool закрыт')


if __name__ == '__main__':
    asyncio.run(main())
