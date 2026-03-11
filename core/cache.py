"""
8.1.3 Кэширование (Redis опционально)
In-memory кэш с возможностью подключения Redis
"""
import time
from typing import Any, Optional, Dict
from dataclasses import dataclass
import asyncio

# Опциональный импорт Redis
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


@dataclass
class CacheItem:
    """Элемент кэша"""
    value: Any
    expires_at: float


class InMemoryCache:
    """In-memory кэш для одиночного инстанса"""
    
    def __init__(self, default_ttl: int = 300):
        self._cache: Dict[str, CacheItem] = {}
        self._default_ttl = default_ttl
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша"""
        async with self._lock:
            item = self._cache.get(key)
            if item is None:
                return None
            
            if time.time() > item.expires_at:
                del self._cache[key]
                return None
            
            return item.value
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Установить значение в кэш"""
        async with self._lock:
            expires_at = time.time() + (ttl or self._default_ttl)
            self._cache[key] = CacheItem(value=value, expires_at=expires_at)
            return True
    
    async def delete(self, key: str) -> bool:
        """Удалить значение из кэша"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        """Проверить существование ключа"""
        return await self.get(key) is not None
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Инкремент значения"""
        async with self._lock:
            item = self._cache.get(key)
            if item is None:
                self._cache[key] = CacheItem(
                    value=amount,
                    expires_at=time.time() + self._default_ttl
                )
                return amount
            
            new_value = item.value + amount
            item.value = new_value
            return new_value
    
    async def clear_expired(self) -> int:
        """Очистка истёкших записей"""
        async with self._lock:
            now = time.time()
            expired = [k for k, v in self._cache.items() if v.expires_at < now]
            for key in expired:
                del self._cache[key]
            return len(expired)
    
    async def get_stats(self) -> Dict:
        """Статистика кэша"""
        async with self._lock:
            now = time.time()
            total = len(self._cache)
            expired = sum(1 for v in self._cache.values() if v.expires_at < now)
            return {
                "total_items": total,
                "expired_items": expired,
                "active_items": total - expired
            }


class RedisCache:
    """Redis кэш для масштабирования"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", default_ttl: int = 300):
        self._redis_url = redis_url
        self._default_ttl = default_ttl
        self._client: Optional[redis.Redis] = None
    
    async def connect(self) -> bool:
        """Подключение к Redis"""
        if not REDIS_AVAILABLE:
            return False
        
        try:
            self._client = redis.from_url(self._redis_url)
            await self._client.ping()
            return True
        except Exception as e:
            print(f"Redis connection error: {e}")
            self._client = None
            return False
    
    async def disconnect(self):
        """Отключение от Redis"""
        if self._client:
            await self._client.close()
    
    async def get(self, key: str) -> Optional[Any]:
        """Получить значение"""
        if not self._client:
            return None
        
        try:
            value = await self._client.get(key)
            if value is None:
                return None
            # Десериализация (простая реализация)
            import json
            return json.loads(value)
        except:
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Установить значение"""
        if not self._client:
            return False
        
        try:
            import json
            serialized = json.dumps(value)
            await self._client.setex(key, ttl or self._default_ttl, serialized)
            return True
        except:
            return False
    
    async def delete(self, key: str) -> bool:
        """Удалить значение"""
        if not self._client:
            return False
        return bool(await self._client.delete(key))
    
    async def exists(self, key: str) -> bool:
        """Проверить существование"""
        if not self._client:
            return False
        return bool(await self._client.exists(key))
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Инкремент"""
        if not self._client:
            return 0
        return await self._client.incrby(key, amount)


class CacheManager:
    """Менеджер кэша с автоматическим выбором backend"""
    
    def __init__(self, use_redis: bool = False, redis_url: str = None):
        self._use_redis = use_redis and REDIS_AVAILABLE
        self._redis_url = redis_url or "redis://localhost:6379/0"
        
        self._memory_cache = InMemoryCache()
        self._redis_cache: Optional[RedisCache] = None
        
        # Ключи для разных типов данных
        self.KEYS = {
            # Пользователи
            "user": "user:{user_id}",
            "user_stats": "user_stats:{user_id}",
            "user_drones": "user_drones:{user_id}",
            
            # Лимиты
            "rate_limit": "rate_limit:{user_id}:{action}",
            "click_history": "clicks:{user_id}",
            
            # Топы
            "top_level": "top:level",
            "top_mined": "top:mined",
            
            # Предметы
            "item": "item:{item_key}",
            "market_lots": "market:lots",
        }
    
    async def init(self) -> bool:
        """Инициализация кэша"""
        if self._use_redis:
            self._redis_cache = RedisCache(self._redis_url)
            connected = await self._redis_cache.connect()
            if connected:
                print("✅ Redis cache connected")
                return True
            else:
                print("⚠️ Redis not available, using in-memory cache")
        
        print("✅ In-memory cache initialized")
        return True
    
    async def get(self, key: str) -> Optional[Any]:
        """Получить значение"""
        if self._redis_cache:
            return await self._redis_cache.get(key)
        return await self._memory_cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Установить значение"""
        if self._redis_cache:
            return await self._redis_cache.set(key, value, ttl)
        return await self._memory_cache.set(key, value, ttl)
    
    async def delete(self, key: str) -> bool:
        """Удалить значение"""
        if self._redis_cache:
            return await self._redis_cache.delete(key)
        return await self._memory_cache.delete(key)
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Инкремент"""
        if self._redis_cache:
            return await self._redis_cache.increment(key, amount)
        return await self._memory_cache.increment(key, amount)
    
    # Удобные методы для кэширования пользователей
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Получить пользователя из кэша"""
        key = self.KEYS["user"].format(user_id=user_id)
        return await self.get(key)
    
    async def set_user(self, user_id: int, data: Dict, ttl: int = 60) -> bool:
        """Сохранить пользователя в кэш"""
        key = self.KEYS["user"].format(user_id=user_id)
        return await self.set(key, data, ttl)
    
    async def invalidate_user(self, user_id: int) -> bool:
        """Инвалидировать кэш пользователя"""
        key = self.KEYS["user"].format(user_id=user_id)
        return await self.delete(key)


# Глобальный экземпляр
cache = CacheManager(use_redis=False)
