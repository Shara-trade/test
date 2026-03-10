"""
8.1.4, 8.3.3 Фоновые процессы через APScheduler
Воркер для фоновых задач (пассивный доход, контейнеры, экспедиции)
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class BackgroundWorker:
    """Воркер для фоновых задач"""
    
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._running = False
    
    async def start(self):
        """Запуск планировщика"""
        if self._running:
            return
        
        self.scheduler = AsyncIOScheduler()
        
        # Регистрация задач
        self._register_jobs()
        
        self.scheduler.start()
        self._running = True
        logger.info("🔄 Background worker started")
    
    async def stop(self):
        """Остановка планировщика"""
        if self.scheduler and self._running:
            self.scheduler.shutdown(wait=True)
            self._running = False
            logger.info("⏹ Background worker stopped")
    
    def _register_jobs(self):
        """Регистрация всех фоновых задач"""
        
        # 1. Пассивный доход дронов (каждые 5 секунд)
        self.scheduler.add_job(
            self._drone_income_tick,
            trigger=IntervalTrigger(seconds=5),
            id="drone_income",
            name="Пассивный доход дронов",
            replace_existing=True
        )
        
        # 2. Восстановление энергии (каждую минуту)
        self.scheduler.add_job(
            self._energy_regen_tick,
            trigger=IntervalTrigger(minutes=1),
            id="energy_regen",
            name="Восстановление энергии",
            replace_existing=True
        )
        
        # 2.1 Остывание перегрева (каждую секунду)
        self.scheduler.add_job(
            self._heat_cooldown_tick,
            trigger=IntervalTrigger(seconds=1),
            id="heat_cooldown",
            name="Остывание перегрева",
            replace_existing=True
        )
        
        # 3. Проверка контейнеров (каждую минуту)
        self.scheduler.add_job(
            self._check_containers,
            trigger=IntervalTrigger(minutes=1),
            id="containers_check",
            name="Проверка контейнеров",
            replace_existing=True
        )
        
        # 4. Проверка экспедиций (каждые 5 минут)
        self.scheduler.add_job(
            self._check_expeditions,
            trigger=IntervalTrigger(minutes=5),
            id="expeditions_check",
            name="Проверка экспедиций",
            replace_existing=True
        )
        
        # 5. Очистка истёкших лотов рынка (каждый час)
        self.scheduler.add_job(
            self._clean_market,
            trigger=IntervalTrigger(hours=1),
            id="market_clean",
            name="Очистка рынка",
            replace_existing=True
        )
        
        # 6. Сброс ежедневных заданий (в 00:00)
        self.scheduler.add_job(
            self._reset_daily_tasks,
            trigger=CronTrigger(hour=0, minute=0),
            id="daily_reset",
            name="Сброс ежедневных заданий",
            replace_existing=True
        )
        
        # 7. Очистка кэша (каждые 10 минут)
        self.scheduler.add_job(
            self._clean_cache,
            trigger=IntervalTrigger(minutes=10),
            id="cache_clean",
            name="Очистка кэша",
            replace_existing=True
        )
        
        # 8. Автоматические ивенты в чатах (каждые 3 часа)
        self.scheduler.add_job(
            self._auto_chat_events,
            trigger=IntervalTrigger(hours=3),
            id="chat_events",
            name="Авто-ивенты в чатах",
            replace_existing=True
        )
        
        # 9. Клановые боссы (раз в сутки)
        self.scheduler.add_job(
            self._spawn_clan_bosses,
            trigger=CronTrigger(hour=12, minute=0),
            id="clan_bosses",
            name="Спавн клановых боссов",
            replace_existing=True
        )
        
        # 10. Обновление топов (каждые 5 минут)
        self.scheduler.add_job(
            self._update_leaderboards,
            trigger=IntervalTrigger(minutes=5),
            id="leaderboards",
            name="Обновление топов",
            replace_existing=True
        )
        
        logger.info(f"📋 Registered {len(self.scheduler.get_jobs())} background jobs")
    
    # ==================== ЗАДАЧИ ====================
    
    async def _drone_income_tick(self):
        """Тик пассивного дохода дронов"""
        try:
            from database import db
            import aiosqlite
            
            async with aiosqlite.connect(db.db_path) as conn:
                # Получаем активных игроков (заходили за 24 часа)
                yesterday = datetime.now() - timedelta(hours=24)
                
                await conn.execute("""
                    UPDATE users 
                    SET metal = metal + (
                        SELECT COALESCE(SUM(d.income_per_tick * (1 + d.level * 0.5)), 0)
                        FROM drones d
                        WHERE d.user_id = users.user_id AND d.is_active = 1
                    )
                    WHERE last_activity >= ?
                """, (yesterday.isoformat(),))
                
                await conn.commit()
                
        except Exception as e:
            logger.error(f"Drone income tick error: {e}")
    
    async def _energy_regen_tick(self):
        """Восстановление энергии"""
        try:
            from database import db
            import aiosqlite
            
            async with aiosqlite.connect(db.db_path) as conn:
                # +5 энергии в минуту всем, у кого не максимум
                await conn.execute("""
                    UPDATE users 
                    SET energy = MIN(energy + 5, max_energy)
                    WHERE energy < max_energy
                """)
                
                await conn.commit()
                
        except Exception as e:
            logger.error(f"Energy regen error: {e}")
    
    async def _heat_cooldown_tick(self):
        """Остывание перегрева"""
        try:
            from database import db
            import aiosqlite
            
            async with aiosqlite.connect(db.db_path) as conn:
                # Остывает только если НЕТ активной блокировки
                # -1 перегрев в секунду для всех с перегревом > 0 и без блокировки
                await conn.execute("""
                    UPDATE users 
                    SET heat = MAX(0, heat - 1)
                    WHERE heat > 0
                    AND (heat_blocked_until IS NULL OR heat_blocked_until <= datetime('now'))
                """)
                
                # Очищаем истёкшие блокировки
                await conn.execute("""
                    UPDATE users 
                    SET heat_blocked_until = NULL
                    WHERE heat_blocked_until IS NOT NULL 
                    AND heat_blocked_until <= datetime('now')
                """)
                
                await conn.commit()
                
        except Exception as e:
            logger.error(f"Heat cooldown error: {e}")
    
    async def _check_containers(self):
        """Проверка готовности контейнеров"""
        try:
            from database import db
            import aiosqlite
            
            async with aiosqlite.connect(db.db_path) as conn:
                now = datetime.now().isoformat()
                
                await conn.execute("""
                    UPDATE containers 
                    SET status = 'ready'
                    WHERE status = 'locked' AND unlock_time <= ?
                """, (now,))
                
                await conn.commit()
                
        except Exception as e:
            logger.error(f"Container check error: {e}")
    
    async def _check_expeditions(self):
        """Проверка завершения экспедиций"""
        try:
            from database import db
            import aiosqlite
            
            async with aiosqlite.connect(db.db_path) as conn:
                now = datetime.now().isoformat()
                
                await conn.execute("""
                    UPDATE expeditions 
                    SET status = 'completed'
                    WHERE status = 'active' AND end_time <= ?
                """, (now,))
                
                await conn.commit()
                
        except Exception as e:
            logger.error(f"Expedition check error: {e}")
    
    async def _clean_market(self):
        """Очистка истёкших лотов"""
        try:
            from database import db
            import aiosqlite
            
            async with aiosqlite.connect(db.db_path) as conn:
                # Лоты старше 7 дней
                week_ago = (datetime.now() - timedelta(days=7)).isoformat()
                
                await conn.execute("""
                    UPDATE market 
                    SET status = 'expired'
                    WHERE status = 'active' AND created_at <= ?
                """, (week_ago,))
                
                await conn.commit()
                
        except Exception as e:
            logger.error(f"Market clean error: {e}")
    
    async def _reset_daily_tasks(self):
        """Сброс ежедневных заданий"""
        try:
            from database import db
            import aiosqlite
            
            async with aiosqlite.connect(db.db_path) as conn:
                # Удаляем старые задания
                await conn.execute("""
                    DELETE FROM user_tasks 
                    WHERE assigned_date < date('now')
                """)
                
                await conn.commit()
                logger.info("📅 Daily tasks reset")
                
        except Exception as e:
            logger.error(f"Daily tasks reset error: {e}")
    
    async def _clean_cache(self):
        """Очистка истёкших записей кэша"""
        try:
            from core.cache import cache
            
            if hasattr(cache._memory_cache, 'clear_expired'):
                cleared = await cache._memory_cache.clear_expired()
                if cleared > 0:
                    logger.debug(f"🗑 Cleaned {cleared} expired cache items")
                    
        except Exception as e:
            logger.error(f"Cache clean error: {e}")
    
    async def _auto_chat_events(self):
        """Автоматические ивенты в чатах"""
        try:
            # Заглушка - будет реализовано с хранением чатов
            logger.debug("🚀 Auto chat events check")
        except Exception as e:
            logger.error(f"Chat events error: {e}")
    
    async def _spawn_clan_bosses(self):
        """Спавн клановых боссов"""
        try:
            from database import db
            import aiosqlite
            
            async with aiosqlite.connect(db.db_path) as conn:
                # Получаем все активные кланы
                async with conn.execute(
                    "SELECT clan_id FROM clans"
                ) as cursor:
                    clans = await cursor.fetchall()
                
                # Для каждого клана спавним босса
                for (clan_id,) in clans:
                    # Проверяем, нет ли уже активного босса
                    async with conn.execute(
                        "SELECT 1 FROM clan_bosses WHERE clan_id = ? AND status = 'active'",
                        (clan_id,)
                    ) as cursor:
                        if await cursor.fetchone():
                            continue
                    
                    # Спавним нового босса
                    await conn.execute("""
                        INSERT INTO clan_bosses (clan_id, boss_key, level, hp, max_hp, status)
                        VALUES (?, 'daily_boss', 1, 10000, 10000, 'active')
                    """, (clan_id,))
                
                await conn.commit()
                logger.info(f"👾 Spawned bosses for {len(clans)} clans")
                
        except Exception as e:
            logger.error(f"Clan boss spawn error: {e}")
    
    async def _update_leaderboards(self):
        """Обновление топов в кэше"""
        try:
            from database import db
            from core.cache import cache
            import aiosqlite
            
            async with aiosqlite.connect(db.db_path) as conn:
                conn.row_factory = aiosqlite.Row
                
                # Топ по уровню
                async with conn.execute("""
                    SELECT user_id, username, level
                    FROM users
                    ORDER BY level DESC
                    LIMIT 100
                """) as cursor:
                    top_level = [dict(r) for r in await cursor.fetchall()]
                    await cache.set("top:level", top_level, ttl=300)
                
                # Топ по добыче
                async with conn.execute("""
                    SELECT user_id, username, total_mined
                    FROM users
                    ORDER BY total_mined DESC
                    LIMIT 100
                """) as cursor:
                    top_mined = [dict(r) for r in await cursor.fetchall()]
                    await cache.set("top:mined", top_mined, ttl=300)
                
        except Exception as e:
            logger.error(f"Leaderboard update error: {e}")
    
    def get_jobs_info(self) -> list:
        """Получить информацию о задачах"""
        if not self.scheduler:
            return []
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return jobs


# Глобальный экземпляр
worker = BackgroundWorker()
