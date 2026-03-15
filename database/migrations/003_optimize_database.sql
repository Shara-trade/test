-- Migration: optimize_database
-- Created: 2025-01-14
-- Description: Оптимизация базы данных через PRAGMA настройки

-- Эти настройки применяются при каждом соединении в pool.py
-- Здесь документируем рекомендуемые настройки SQLite

-- WAL режим для лучшей конкурентности
-- PRAGMA journal_mode=WAL;

-- Нормальный режим синхронизации (быстрее, но безопасно для WAL)
-- PRAGMA synchronous=NORMAL;

-- Увеличенный кэш (10000 страниц ~ 40MB)
-- PRAGMA cache_size=10000;

-- Хранение временных данных в памяти
-- PRAGMA temp_store=MEMORY;

-- Оптимизация для частых чтений
-- PRAGMA mmap_size=268435456;  -- 256MB

-- Rollback: настройки PRAGMA не требуют отката
