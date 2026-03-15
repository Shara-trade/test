-- Migration: add_container_unlock_times
-- Created: 2025-01-14
-- Description: Добавляет время разблокировки контейнеров

-- Добавляем колонку unlock_minutes в контейнеры если нужно
-- (уже есть в schema.sql, но для существующих данных)

-- Обновляем время разблокировки для существующих типов контейнеров
-- Это делается через код, здесь только для документации

-- Rollback (copy to rollback/002_add_container_unlock_times.sql):
-- No rollback needed - this is a documentation migration
