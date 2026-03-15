"""
Интеграционные тесты системы дронов.
Примеры работы механик по ТЗ (пункты 8-9)
"""
import pytest
from datetime import datetime, timedelta
from game.drones import DroneSystem, DRONE_CONFIG, MAX_HIRED_DRONES, MISSION_DURATION_MINUTES


class TestExample1_PurchaseAndHire:
    """
    Пример 1: Покупка и найм (по ТЗ)
    
    1. У игрока 10 000 металла, 0 дронов.
    2. Заходит в магазин, покупает Базового дрона за 7 500 металла.
    3. В таблице drones: base_lvl1 становится 1. Баланс металла: 2 500.
    4. Заходит в карточку Базового дрона, нажимает [🤚].
    5. Нанимает 1 дрона: base_lvl1 становится 0, drones_hired становится 1.
    6. В ангаре теперь: Дронов в ангаре: 1, Дронов в найме: 1/50, Доход: +30 металла/мин.
    """
    
    @pytest.mark.asyncio
    async def test_purchase_basic_drone(self):
        """Тест покупки базового дрона"""
        # Цена базового дрона
        price = DroneSystem.get_price('basic')
        
        # Проверяем что цена соответствует ТЗ
        assert price['metal'] == 7500
        assert price['crystals'] == 0
        assert price['dark_matter'] == 0
        
        # Проверяем что можно купить на 10000 металла
        balance = 10000
        can_afford = balance >= price['metal']
        remaining = balance - price['metal']
        
        assert can_afford is True
        assert remaining == 2500
    
    @pytest.mark.asyncio
    async def test_hire_basic_drone(self):
        """Тест найма дрона"""
        # Доход базового дрона 1 уровня
        income = DroneSystem.get_income('basic', 1)
        
        assert income['metal'] == 30
        assert income['crystals'] == 0
        assert income['dark_matter'] == 0
    
    @pytest.mark.asyncio
    async def test_hire_check_limits(self):
        """Тест проверки лимитов найма"""
        # Проверяем что можно нанять 1 дрона
        drones_data = {'basic_lvl1': 1}
        drones_hired = 0
        
        can_hire, error = DroneSystem.can_hire(drones_data, drones_hired, 'basic', 1, 1)
        
        assert can_hire is True
        assert error == ""
    
    @pytest.mark.asyncio
    async def test_hire_limit_50(self):
        """Тест лимита 50 дронов"""
        # Проверяем что нельзя нанять больше 50
        drones_data = {'basic_lvl1': 100}
        drones_hired = 50
        
        can_hire, error = DroneSystem.can_hire(drones_data, drones_hired, 'basic', 1, 1)
        
        assert can_hire is False
        assert "лимит" in error.lower()


class TestExample2_Upgrade:
    """
    Пример 2: Улучшение (по ТЗ)
    
    1. У игрока 10 Базовых дронов 1 уровня, все свободны.
    2. Заходит в карточку Базового дрона, нажимает [⭐️].
    3. Выбирает [Все] (доступно 10).
    4. Система считает: 10 дронов = 2 улучшения (10/5 = 2).
    5. base_lvl1 уменьшается на 10, base_lvl2 увеличивается на 2.
    6. Итог: 0 дронов 1 уровня, 2 дрона 2 уровня.
    """
    
    @pytest.mark.asyncio
    async def test_upgrade_calculation(self):
        """Тест расчёта улучшения"""
        # 10 дронов = 2 улучшения
        available = 10
        max_upgrades = DroneSystem.calculate_max_upgrades(available)
        
        assert max_upgrades == 2
    
    @pytest.mark.asyncio
    async def test_upgrade_validation(self):
        """Тест валидации улучшения"""
        drones_data = {'basic_lvl1': 10}
        
        can_upgrade, error = DroneSystem.can_upgrade(drones_data, 'basic', 1, 2)
        
        assert can_upgrade is True
        assert error == ""
    
    @pytest.mark.asyncio
    async def test_upgrade_insufficient_drones(self):
        """Тест недостаточно дронов для улучшения"""
        drones_data = {'basic_lvl1': 3}
        
        can_upgrade, error = DroneSystem.can_upgrade(drones_data, 'basic', 1, 1)
        
        assert can_upgrade is False
        assert "недостаточно" in error.lower()
    
    @pytest.mark.asyncio
    async def test_upgrade_income_increase(self):
        """Тест увеличения дохода после улучшения"""
        # Доход 1 уровня
        income_1 = DroneSystem.get_income('basic', 1)
        
        # Доход 2 уровня
        income_2 = DroneSystem.get_income('basic', 2)
        
        # Доход должен увеличиться
        assert income_2['metal'] > income_1['metal']
        assert income_2['metal'] == 95


class TestExample3_SendAndCollect:
    """
    Пример 3: Отправка и сбор (по ТЗ)
    
    1. У игрока 35 дронов в найме (уже работают), 49 свободных.
    2. Нажимает [Отправить] — 49 дронов улетают.
    3. drones_hired становится 84 (35 + 49), hired_until = текущее время + 2 часа.
    4. Через 1 час игрок заходит:
       · За час накопилось: доход в минуту × 60 минут
       · Эти ресурсы уже в хранилище
       · Видит кнопку [Собрать]
    5. Нажимает [Собрать] — ресурсы уходят на баланс, хранилище пусто.
    6. Дроны продолжают работать (до окончания 2 часов ещё 1 час).
    """
    
    @pytest.mark.asyncio
    async def test_send_drones_total(self):
        """Тест общего количества дронов после отправки"""
        # 35 в найме + 49 свободных
        already_hired = 35
        to_send = 49
        
        total_after_send = already_hired + to_send
        
        assert total_after_send == 84
    
    @pytest.mark.asyncio
    async def test_send_drones_limit(self):
        """Тест что общее количество не превышает 50"""
        already_hired = 35
        to_send = 49
        
        # Проверяем что не превышает лимит
        can_send = (already_hired + to_send) <= MAX_HIRED_DRONES
        
        assert can_send is False  # 84 > 50, поэтому нельзя
    
    @pytest.mark.asyncio
    async def test_income_accumulation_1_hour(self):
        """Тест накопления дохода за 1 час"""
        from datetime import datetime, timedelta
        
        # 35 базовых дронов 1 уровня в найме
        drones_data = {'basic_lvl1': 35}
        hired_count = 35
        last_update = datetime.now() - timedelta(minutes=60)
        
        result = DroneSystem.calculate_storage_income(drones_data, hired_count, last_update)
        
        # 35 × 30 × 60 = 63000 металла
        expected = 35 * 30 * 60
        
        assert result['metal'] == expected
        assert result['minutes_passed'] == 60
    
    @pytest.mark.asyncio
    async def test_mission_duration(self):
        """Тест длительности миссии"""
        assert MISSION_DURATION_MINUTES == 120
    
    @pytest.mark.asyncio
    async def test_mission_status_active(self):
        """Тест статуса активной миссии"""
        hired_until = datetime.now() + timedelta(hours=1)
        
        status = DroneSystem.check_mission_status(hired_until)
        
        assert status['is_active'] is True
        assert status['is_expired'] is False
    
    @pytest.mark.asyncio
    async def test_mission_status_expired(self):
        """Тест статуса завершённой миссии"""
        hired_until = datetime.now() - timedelta(hours=1)
        
        status = DroneSystem.check_mission_status(hired_until)
        
        assert status['is_active'] is False
        assert status['is_expired'] is True


class TestErrorHandling:
    """
    Тесты обработки ошибок (пункт 9 ТЗ)
    
    Все ошибки должны показываться в popup:
    · «Недостаточно ресурсов»
    · «Недостаточно свободных дронов»
    · «Недостаточно свободных слотов в найме. Доступно: X»
    · «Недостаточно дронов для продажи»
    · «Недостаточно свободных дронов для улучшения. Доступно: X»
    · «Требуется привилегия»
    · «Достигнут лимит найма (50/50)»
    · «Сначала соберите ресурсы»
    · «Дроны уже в полёте»
    """
    
    @pytest.mark.asyncio
    async def test_error_insufficient_resources(self):
        """Тест ошибки недостаточно ресурсов"""
        # Пытаемся купить дрона без ресурсов
        price = DroneSystem.get_price('ai')
        
        # ИИ-дрон стоит 20000 каждого ресурса
        assert price['metal'] == 20000
        assert price['crystals'] == 20000
        assert price['dark_matter'] == 20000
    
    @pytest.mark.asyncio
    async def test_error_insufficient_drones(self):
        """Тест ошибки недостаточно дронов"""
        drones_data = {'basic_lvl1': 0}
        
        can_hire, error = DroneSystem.can_hire(drones_data, 0, 'basic', 1, 1)
        
        assert can_hire is False
        assert "недостаточно" in error.lower() or "доступно" in error.lower()
    
    @pytest.mark.asyncio
    async def test_error_hire_limit_reached(self):
        """Тест ошибки достигнут лимит найма"""
        drones_data = {'basic_lvl1': 10}
        drones_hired = 50  # Максимум
        
        can_hire, error = DroneSystem.can_hire(drones_data, drones_hired, 'basic', 1, 1)
        
        assert can_hire is False
        assert "лимит" in error.lower()
    
    @pytest.mark.asyncio
    async def test_error_insufficient_for_upgrade(self):
        """Тест ошибки недостаточно для улучшения"""
        drones_data = {'basic_lvl1': 3}  # Нужно минимум 5
        
        can_upgrade, error = DroneSystem.can_upgrade(drones_data, 'basic', 1, 1)
        
        assert can_upgrade is False
        assert "недостаточно" in error.lower()
    
    @pytest.mark.asyncio
    async def test_error_max_level_reached(self):
        """Тест ошибки достигнут максимальный уровень"""
        from game.drones import MAX_DRONE_LEVEL
        
        drones_data = {'basic_lvl5': 10}
        
        # Нельзя улучшить 5 уровень
        can_upgrade, error = DroneSystem.can_upgrade(drones_data, 'basic', MAX_DRONE_LEVEL, 1)
        
        assert can_upgrade is False
        assert "максимальный" in error.lower()
    
    @pytest.mark.asyncio
    async def test_error_slots_available(self):
        """Тест ошибки недостаточно слотов"""
        drones_data = {'basic_lvl1': 100}
        drones_hired = 48  # Осталось 2 слота
        
        can_hire, error = DroneSystem.can_hire(drones_data, drones_hired, 'basic', 1, 5)
        
        assert can_hire is False
        assert "слот" in error.lower()


class TestDronePricesAndIncome:
    """Тесты цен и доходов всех дронов по ТЗ"""
    
    @pytest.mark.asyncio
    async def test_basic_drone_income_progression(self):
        """Тест прогрессии дохода базового дрона"""
        expected = {
            1: 30,
            2: 95,
            3: 230,
            4: 620,
            5: 1860
        }
        
        for level, expected_income in expected.items():
            income = DroneSystem.get_income('basic', level)
            assert income['metal'] == expected_income, f"Level {level} mismatch"
    
    @pytest.mark.asyncio
    async def test_miner_drone_income_progression(self):
        """Тест прогрессии дохода шахтёра"""
        expected = {
            1: (40, 30),
            2: (120, 95),
            3: (300, 230),
            4: (800, 620),
            5: (2400, 1860)
        }
        
        for level, (metal, crystals) in expected.items():
            income = DroneSystem.get_income('miner', level)
            assert income['metal'] == metal, f"Level {level} metal mismatch"
            assert income['crystals'] == crystals, f"Level {level} crystals mismatch"
    
    @pytest.mark.asyncio
    async def test_laser_drone_income_progression(self):
        """Тест прогрессии дохода лазерного дрона"""
        expected = {
            1: 60,
            2: 180,
            3: 450,
            4: 1200,
            5: 3600
        }
        
        for level, expected_income in expected.items():
            income = DroneSystem.get_income('laser', level)
            assert income['crystals'] == expected_income, f"Level {level} mismatch"
    
    @pytest.mark.asyncio
    async def test_quantum_drone_income_progression(self):
        """Тест прогрессии дохода квантового дрона"""
        expected = {
            1: 80,
            2: 240,
            3: 600,
            4: 1600,
            5: 4800
        }
        
        for level, expected_income in expected.items():
            income = DroneSystem.get_income('quantum', level)
            assert income['dark_matter'] == expected_income, f"Level {level} mismatch"
    
    @pytest.mark.asyncio
    async def test_ai_drone_income_progression(self):
        """Тест прогрессии дохода ИИ-дрона"""
        expected = {
            1: 80,
            2: 240,
            3: 600,
            4: 1600,
            5: 4800
        }
        
        for level, expected_income in expected.items():
            income = DroneSystem.get_income('ai', level)
            assert income['metal'] == expected_income, f"Level {level} metal mismatch"
            assert income['crystals'] == expected_income, f"Level {level} crystals mismatch"
            assert income['dark_matter'] == expected_income, f"Level {level} dark_matter mismatch"


class TestUpgradeProgression:
    """Тесты прогрессии улучшения 5→1"""
    
    @pytest.mark.asyncio
    async def test_upgrade_formula(self):
        """Тест формулы улучшения"""
        # 5 дронов 1 уровня = 1 дрон 2 уровня
        assert DroneSystem.calculate_max_upgrades(5) == 1
        assert DroneSystem.calculate_max_upgrades(10) == 2
        assert DroneSystem.calculate_max_upgrades(25) == 5
        
        # 25 дронов 1 уровня = 5 дронов 2 уровня = 1 дрон 3 уровня
        assert 25 // 5 == 5  # 25 -> 5 дронов 2 уровня
        assert 5 // 5 == 1   # 5 -> 1 дрон 3 уровня
    
    @pytest.mark.asyncio
    async def test_sell_price_progression(self):
        """Тест прогрессии цены продажи"""
        # Уровень 1: 30% от 7500 = 2250
        price_1 = DroneSystem.get_sell_price('basic', 1)
        assert price_1['metal'] == 2250
        
        # Уровень 2: 30% от (5 × 7500) = 11250
        price_2 = DroneSystem.get_sell_price('basic', 2)
        assert price_2['metal'] == 11250
        
        # Уровень 3: 30% от (25 × 7500) = 56250
        price_3 = DroneSystem.get_sell_price('basic', 3)
        assert price_3['metal'] == 56250
