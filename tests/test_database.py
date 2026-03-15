"""
Тесты базы данных.
"""
import pytest
import aiosqlite


class TestDatabaseManager:
    """Тесты DatabaseManager"""
    
    @pytest.mark.asyncio
    async def test_create_user(self, db, test_user):
        """Тест создания пользователя"""
        user = await db.get_user(test_user)
        
        assert user is not None
        assert user['user_id'] == test_user
        assert user['username'] == 'test_user'
        assert user['level'] == 1
    
    @pytest.mark.asyncio
    async def test_user_not_exists(self, db):
        """Тест несуществующего пользователя"""
        user = await db.get_user(123456789)
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_update_resources(self, db, test_user):
        """Тест обновления ресурсов"""
        await db.update_user_resources(
            test_user,
            metal=500,
            crystals=50,
            dark_matter=5
        )
        
        user = await db.get_user(test_user)
        
        assert user['metal'] == 500
        assert user['crystals'] == 50
        assert user['dark_matter'] == 5
    
    @pytest.mark.asyncio
    async def test_add_experience(self, db, test_user):
        """Тест добавления опыта"""
        result = await db.add_experience(test_user, 500)
        
        assert result['success'] is True
        assert result['exp_added'] == 500
    
    @pytest.mark.asyncio
    async def test_level_up(self, db, test_user):
        """Тест повышения уровня"""
        # Добавляем много опыта
        await db.add_experience(test_user, 10000)
        
        user = await db.get_user(test_user)
        
        # При 10000 опыта должен быть уровень > 1
        assert user['level'] > 1
    
    @pytest.mark.asyncio
    async def test_get_user_full_profile(self, db, test_user_with_resources):
        """Тест получения полного профиля"""
        profile = await db.get_user_full_profile(test_user_with_resources)
        
        assert profile is not None
        assert profile['user_id'] == test_user_with_resources
        assert 'drones_count' in profile
        assert 'items_count' in profile
        assert 'containers_count' in profile
    
    @pytest.mark.asyncio
    async def test_add_item(self, db, test_user):
        """Тест добавления предмета"""
        # Сначала добавляем предмет в каталог
        async with aiosqlite.connect(db.db_path) as conn:
            await conn.execute(
                "INSERT OR IGNORE INTO items (item_key, name, rarity, icon) VALUES (?, ?, ?, ?)",
                ("test_item", "Test Item", "common", "📦")
            )
            await conn.commit()
        
        result = await db.add_item(test_user, "test_item", quantity=5)
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_remove_item(self, db, test_user):
        """Тест удаления предмета"""
        # Сначала добавляем предмет в каталог
        async with aiosqlite.connect(db.db_path) as conn:
            await conn.execute(
                "INSERT OR IGNORE INTO items (item_key, name, rarity, icon) VALUES (?, ?, ?, ?)",
                ("test_item", "Test Item", "common", "📦")
            )
            await conn.commit()

        await db.add_item(test_user, "test_item", quantity=5)
        result = await db.remove_item(test_user, "test_item", quantity=3)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_remove_item_not_enough(self, db, test_user):
        """Тест удаления предмета при недостатке"""
        # Сначала добавляем предмет в каталог
        async with aiosqlite.connect(db.db_path) as conn:
            await conn.execute(
                "INSERT OR IGNORE INTO items (item_key, name, rarity, icon) VALUES (?, ?, ?, ?)",
                ("test_item", "Test Item", "common", "📦")
            )
            await conn.commit()
        
        await db.add_item(test_user, "test_item", quantity=2)
        result = await db.remove_item(test_user, "test_item", quantity=5)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_top_players(self, db, test_user):
        """Тест получения топа игроков"""
        top = await db.get_top_players(category="level", limit=10)
        
        assert isinstance(top, list)
    
    @pytest.mark.asyncio
    async def test_get_user_rank(self, db, test_user):
        """Тест получения ранга игрока"""
        rank = await db.get_user_rank(test_user, category="level")
        
        assert rank > 0


class TestDatabaseTransactions:
    """Тесты транзакций БД"""
    
    @pytest.mark.asyncio
    async def test_atomic_update(self, db, test_user):
        """Тест атомарного обновления"""
        # Обновляем несколько ресурсов одновременно
        await db.update_user_resources(
            test_user,
            metal=1000,
            crystals=100,
            dark_matter=10
        )
        
        user = await db.get_user(test_user)
        
        assert user['metal'] == 1000
        assert user['crystals'] == 100
        assert user['dark_matter'] == 10
    
    @pytest.mark.asyncio
    async def test_experience_formula(self, db):
        """Тест формулы опыта"""
        # Проверяем формулу: 1000 * level * (1 + 0.1 * level)
        # Level 1: 1000 * 1 * 1.1 = 1100
        # Level 10: 1000 * 10 * 2.0 = 20000
        # Level 100: 1000 * 100 * 11 = 1,100,000
        
        # Level 1
        exp_1 = db._exp_for_level(1)
        assert exp_1 == 1100
        
        # Level 10
        exp_10 = db._exp_for_level(10)
        assert exp_10 == 20000
        
        # Level 100
        exp_100 = db._exp_for_level(100)
        assert exp_100 == 1100000


class TestDatabaseIntegrity:
    """Тесты целостности БД"""
    
    @pytest.mark.asyncio
    async def test_unique_constraint(self, db, test_user):
        """Тест уникальности"""
        # Пытаемся создать пользователя с тем же ID
        result = await db.create_user(
            user_id=test_user,
            username="another_user",
            first_name="Another"
        )
        
        # Должно вернуть False (пользователь уже существует)
        assert result is False
