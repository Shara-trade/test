"""
Connection Pool для SQLite.
Оптимизация производительности базы данных.
"""
import asyncio
import aiosqlite
import logging
from typing import Optional
from contextlib import asynccontextmanager

logger = logging.getLogger("database.pool")


class ConnectionPool:
    """
    Пул соединений для SQLite.
    
    Вместо создания нового соединения на каждый запрос,
    переиспользует существующие соединения.
    
    Usage:
        pool = ConnectionPool("database.db", max_connections=10)
        
        async with pool.acquire() as conn:
            async with conn.execute("SELECT * FROM users") as cursor:
                rows = await cursor.fetchall()
    """
    
    def __init__(self, db_path: str, max_connections: int = 10):
        self.db_path = db_path
        self.max_connections = max_connections
        self._pool: asyncio.Queue = asyncio.Queue(max_connections)
        self._connections: list = []
        self._lock = asyncio.Lock()
        self._initialized = False
    
    async def initialize(self):
        """Инициализировать пул соединений"""
        if self._initialized:
            return
        
        async with self._lock:
            if self._initialized:
                return
            
            for _ in range(min(3, self.max_connections)):
                conn = await self._create_connection()
                await self._pool.put(conn)
            
            self._initialized = True
            logger.info(f"Connection pool initialized with {self._pool.qsize()} connections")
    
    async def _create_connection(self) -> aiosqlite.Connection:
        """Создать новое соединение"""
        conn = await aiosqlite.connect(self.db_path)
        conn.row_factory = aiosqlite.Row
        
        # Оптимизации SQLite
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA synchronous=NORMAL")
        await conn.execute("PRAGMA cache_size=10000")
        await conn.execute("PRAGMA temp_store=MEMORY")
        
        self._connections.append(conn)
        return conn
    
    async def acquire(self) -> aiosqlite.Connection:
        """
        Получить соединение из пула.
        Если пул пуст, создаёт новое соединение.
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Пытаемся получить из пула с таймаутом
            conn = await asyncio.wait_for(
                self._pool.get(),
                timeout=1.0
            )
            return conn
        except asyncio.TimeoutError:
            # Пул пуст, создаём новое если не достигнут лимит
            async with self._lock:
                if len(self._connections) < self.max_connections:
                    logger.debug("Creating new connection (pool exhausted)")
                    return await self._create_connection()
            
            # Ждём пока освободится
            return await self._pool.get()
    
    async def release(self, conn: aiosqlite.Connection):
        """Вернуть соединение в пул"""
        if self._initialized:
            try:
                await self._pool.put(conn)
            except asyncio.QueueFull:
                # Пул переполнен, закрываем соединение
                await conn.close()
                if conn in self._connections:
                    self._connections.remove(conn)
    
    @asynccontextmanager
    async def connection(self):
        """Контекстный менеджер для соединения"""
        conn = await self.acquire()
        try:
            yield conn
        finally:
            await self.release(conn)
    
    async def close(self):
        """Закрыть все соединения"""
        self._initialized = False
        
        for conn in self._connections:
            try:
                await conn.close()
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
        
        self._connections.clear()
        
        # Очищаем очередь
        while not self._pool.empty():
            try:
                self._pool.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        logger.info("Connection pool closed")
    
    @property
    def stats(self) -> dict:
        """Статистика пула"""
        return {
            "total_connections": len(self._connections),
            "available": self._pool.qsize(),
            "in_use": len(self._connections) - self._pool.qsize(),
            "max_connections": self.max_connections
        }


# Глобальный пул (инициализируется при старте)
_pool: Optional[ConnectionPool] = None


def get_pool() -> ConnectionPool:
    """Получить глобальный пул соединений"""
    global _pool
    if _pool is None:
        from config import DATABASE_PATH
        _pool = ConnectionPool(DATABASE_PATH)
    return _pool


async def init_pool(db_path: str = None, max_connections: int = 10):
    """Инициализировать глобальный пул"""
    global _pool
    
    if db_path is None:
        from config import DATABASE_PATH
        db_path = DATABASE_PATH
    
    _pool = ConnectionPool(db_path, max_connections)
    await _pool.initialize()
    return _pool


async def close_pool():
    """Закрыть глобальный пул"""
    global _pool
    
    if _pool:
        await _pool.close()
        _pool = None


@asynccontextmanager
async def get_connection():
    """Получить соединение из глобального пула"""
    pool = get_pool()
    async with pool.connection() as conn:
        yield conn
