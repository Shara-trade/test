"""
Фикстуры для pytest.
"""
import asyncio
import pytest
import aiosqlite
import tempfile
import os
from typing import AsyncGenerator


@pytest.fixture(scope="session")
def event_loop():
    """Создать event loop для сессии"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def temp_db() -> AsyncGenerator[str, None]:
    """
    Создать временную базу данных для тестов.
    
    Yields:
        Путь к временной БД
    """
    # Создаём временный файл
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    # Инициализируем схему
    async with aiosqlite.connect(db_path) as db:
        with open("database/schema.sql", "r", encoding="utf-8") as f:
            await db.executescript(f.read())
        await db.commit()
    
    yield db_path
    
    # Удаляем после теста
    try:
        os.remove(db_path)
    except:
        pass


@pytest.fixture
async def db(temp_db):
    """
    DatabaseManager с временной БД.
    
    Yields:
        DatabaseManager
    """
    from database.db_manager import DatabaseManager
    
    db = DatabaseManager(temp_db)
    yield db


@pytest.fixture
async def test_user(db):
    """
    Создать тестового пользователя.
    
    Yields:
        user_id
    """
    user_id = 999999
    await db.create_user(
        user_id=user_id,
        username="test_user",
        first_name="Test",
        last_name="User"
    )
    yield user_id


@pytest.fixture
async def test_user_with_resources(db, test_user):
    """
    Тестовый пользователь с ресурсами.
    
    Yields:
        user_id
    """
    await db.update_user_resources(
        test_user,
        metal=10000,
        crystals=1000,
        dark_matter=100,
        energy=500
    )
    yield test_user


@pytest.fixture
def mock_callback():
    """
    Мок CallbackQuery.
    """
    from unittest.mock import AsyncMock, MagicMock
    
    callback = MagicMock()
    callback.from_user.id = 999999
    callback.from_user.username = "test_user"
    callback.data = "test_callback"
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.message.answer = AsyncMock()
    callback.answer = AsyncMock()
    
    return callback


@pytest.fixture
def mock_message():
    """
    Мок Message.
    """
    from unittest.mock import AsyncMock, MagicMock
    
    message = MagicMock()
    message.from_user.id = 999999
    message.from_user.username = "test_user"
    message.text = "test message"
    message.answer = AsyncMock()
    message.edit_text = AsyncMock()
    
    return message
