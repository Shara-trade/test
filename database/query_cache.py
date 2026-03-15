"""
Кэширование для частых запросов.
Оптимизация производительности.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger("cache.queries")


class QueryCache:
    """
    Кэш для результатов запросов к БД.
    
    Кэширует:
    - Топы игроков (на 5 минут)
    - Справочники (на 1 час)
    - Профили пользователей (на 30 сек)
    """
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._expiry: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша"""
        async with self._lock:
            if key not in self._cache:
                return None
            
            # Проверяем срок действия
            if key in self._expiry and datetime.now() > self._expiry[key]:
                del self._cache[key]
                del self._expiry[key]
                return None
            
            return self._cache[key]
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """Установить значение в кэш"""
        async with self._lock:
            self._cache[key] = value
            self._expiry[key] = datetime.now() + timedelta(seconds=ttl)
    
    async def delete(self, key: str):
        """Удалить значение из кэша"""
        async with self._lock:
            self._cache.pop(key, None)
            self._expiry.pop(key, None)
    
    async def clear(self):
        """Очистить весь кэш"""
        async with self._lock:
            self._cache.clear()
            self._expiry.clear()
    
    async def cleanup_expired(self):
        """Удалить истёкшие записи"""
        async with self._lock:
            now = datetime.now()
            expired = [k for k, v in self._expiry.items() if now > v]
            
            for key in expired:
                self._cache.pop(key, None)
                self._expiry.pop(key, None)
            
            if expired:
                logger.debug(f"Cleaned up {len(expired)} expired cache entries")


# Глобальный экземпляр
query_cache = QueryCache()


# ===== СПЕЦИАЛИЗИРОВАННЫЕ ФУНКЦИИ =====

async def get_cached_top(category: str, page: int, per_page: int = 10) -> Optional[List[Dict]]:
    """
    Получить кэшированный топ.
    Кэшируется на 5 минут.
    """
    key = f"top:{category}:{page}:{per_page}"
    return await query_cache.get(key)


async def set_cached_top(category: str, page: int, data: List[Dict], per_page: int = 10):
    """Сохранить топ в кэш на 5 минут"""
    key = f"top:{category}:{page}:{per_page}"
    await query_cache.set(key, data, ttl=300)


async def get_cached_items_catalog() -> Optional[List[Dict]]:
    """
    Получить кэшированный справочник предметов.
    Кэшируется на 1 час.
    """
    key = "catalog:items"
    return await query_cache.get(key)


async def set_cached_items_catalog(items: List[Dict]):
    """Сохранить справочник предметов в кэш на 1 час"""
    key = "catalog:items"
    await query_cache.set(key, items, ttl=3600)


async def get_cached_materials() -> Optional[List[Dict]]:
    """
    Получить кэшированный справочник материалов.
    Кэшируется на 1 час.
    """
    key = "catalog:materials"
    return await query_cache.get(key)


async def set_cached_materials(materials: List[Dict]):
    """Сохранить справочник материалов в кэш на 1 час"""
    key = "catalog:materials"
    await query_cache.set(key, materials, ttl=3600)


async def get_cached_user_rank(user_id: int, category: str) -> Optional[int]:
    """
    Получить кэшированный ранг пользователя.
    Кэшируется на 1 минуту.
    """
    key = f"rank:{user_id}:{category}"
    return await query_cache.get(key)


async def set_cached_user_rank(user_id: int, category: str, rank: int):
    """Сохранить ранг пользователя в кэш на 1 минуту"""
    key = f"rank:{user_id}:{category}"
    await query_cache.set(key, rank, ttl=60)


async def invalidate_user_cache(user_id: int):
    """Инвалидировать весь кэш пользователя"""
    # Ранги
    for category in ['level', 'mining', 'wealth', 'clicks']:
        await query_cache.delete(f"rank:{user_id}:{category}")
    
    # Топы (на следующем запросе обновятся)
    # Можно инвалидировать все топы, но это дорого
    # Лучше полагаться на TTL


async def invalidate_tops_cache():
    """Инвалидировать кэш всех топов"""
    # Очищаем все ключи, начинающиеся с "top:"
    async with query_cache._lock:
        keys_to_delete = [k for k in query_cache._cache.keys() if k.startswith("top:")]
        for key in keys_to_delete:
            query_cache._cache.pop(key, None)
            query_cache._expiry.pop(key, None)
