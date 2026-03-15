"""
Тесты системы дронов.
Новая система по ТЗ (dron.txt)
"""
import pytest
from datetime import datetime, timedelta
from game.drones import (
    DroneSystem, DRONE_CONFIG, DRONE_TYPES, LEVEL_EMOJI,
    MAX_DRONE_LEVEL, MAX_HIRED_DRONES, MISSION_DURATION_MINUTES
)


class TestDroneConfig:
    """Тесты конфигурации дронов"""
    
    def test_drone_types_exist(self):
        """Тест наличия всех типов дронов"""
        assert 'basic' in DRONE_CONFIG
        assert 'miner' in DRONE_CONFIG
        assert 'laser' in DRONE_CONFIG
        assert 'quantum' in DRONE_CONFIG
        assert 'ai' in DRONE_CONFIG
    
    def test_drone_config_structure(self):
        """Тест структуры конфигурации дрона"""
        for drone_type, config in DRONE_CONFIG.items():
            assert 'name' in config
            assert 'emoji' in config
            assert 'price' in config
            assert 'income' in config
            
            # Проверяем цены
            assert 'metal' in config['price']
            assert 'crystals' in config['price']
            assert 'dark_matter' in config['price']
            
            # Проверяем доход для всех 5 уровней
            for level in range(1, 6):
                assert level in config['income']
                income = config['income'][level]
                assert 'metal' in income
                assert 'crystals' in income
                assert 'dark_matter' in income
    
    def test_level_emoji(self):
        """Тест эмодзи уровней"""
        assert LEVEL_EMOJI[1] == "⚪️"
        assert LEVEL_EMOJI[2] == "🟢"
        assert LEVEL_EMOJI[3] == "🟣"
        assert LEVEL_EMOJI[4] == "🔴"
        assert LEVEL_EMOJI[5] == "🟡"
    
    def test_module_slots(self):
        """Тест слотов модулей"""
        from game.drones import MODULE_SLOTS
        
        assert MODULE_SLOTS[1] == 0
        assert MODULE_SLOTS[2] == 1
        assert MODULE_SLOTS[3] == 2
        assert MODULE_SLOTS[4] == 3
        assert MODULE_SLOTS[5] == 4


class TestDroneSystemIncome:
    """Тесты расчёта дохода"""
    
    def test_get_income_basic(self):
        """Тест дохода базового дрона"""
        income = DroneSystem.get_income('basic', 1)
        
        assert income['metal'] == 30
        assert income['crystals'] == 0
        assert income['dark_matter'] == 0
    
    def test_get_income_miner(self):
        """Тест дохода шахтёра"""
        income = DroneSystem.get_income('miner', 1)
        
        assert income['metal'] == 40
        assert income['crystals'] == 30
        assert income['dark_matter'] == 0
    
    def test_get_income_ai(self):
        """Тест дохода ИИ-дрона (все ресурсы)"""
        income = DroneSystem.get_income('ai', 5)
        
        assert income['metal'] == 4800
        assert income['crystals'] == 4800
        assert income['dark_matter'] == 4800
    
    def test_income_scales_with_level(self):
        """Тест масштабирования дохода с уровнем"""
        for drone_type in DRONE_TYPES:
            incomes = [DroneSystem.get_income(drone_type, level) for level in range(1, 6)]
            
            # Доход должен расти
            for i in range(1, len(incomes)):
                assert incomes[i]['metal'] > incomes[i-1]['metal'] or incomes[i]['crystals'] > incomes[i-1]['crystals'] or incomes[i]['dark_matter'] > incomes[i-1]['dark_matter']
    
    def test_calculate_income_per_minute_empty(self):
        """Тест дохода без дронов"""
        income = DroneSystem.calculate_income_per_minute({}, 0)
        
        assert income['metal'] == 0
        assert income['crystals'] == 0
        assert income['dark_matter'] == 0
    
    def test_calculate_income_per_minute_single(self):
        """Тест дохода от одного дрона"""
        drones_data = {'basic_lvl1': 1}
        income = DroneSystem.calculate_income_per_minute(drones_data, 1)
        
        assert income['metal'] == 30
        assert income['crystals'] == 0
        assert income['dark_matter'] == 0
    
    def test_calculate_income_per_minute_multiple(self):
        """Тест дохода от нескольких дронов"""
        drones_data = {
            'basic_lvl1': 5,
            'miner_lvl2': 3
        }
        income = DroneSystem.calculate_income_per_minute(drones_data, 8)
        
        # 5 * 30 + 3 * 120 = 150 + 360 = 510 metal
        # 0 + 3 * 95 = 285 crystals
        assert income['metal'] == 510
        assert income['crystals'] == 285


class TestDroneSystemPrices:
    """Тесты цен дронов"""
    
    @pytest.mark.asyncio
    async def test_get_price_basic(self):
        """Тест получения цены базового дрона"""
        price = DroneSystem.get_price('basic')
        assert price['metal'] == 7500
        assert price['crystals'] == 0
        assert price['dark_matter'] == 0
    
    @pytest.mark.asyncio
    async def test_get_price_miner(self):
        """Тест получения цены шахтёра"""
        price = DroneSystem.get_price('miner')
        assert price['metal'] == 10000
        assert price['crystals'] == 7500
        assert price['dark_matter'] == 0
    
    @pytest.mark.asyncio
    async def test_get_price_ai(self):
        """Тест получения цены ИИ-дрона"""
        price = DroneSystem.get_price('ai')
        assert price['metal'] == 20000
        assert price['crystals'] == 20000
        assert price['dark_matter'] == 20000
    
    @pytest.mark.asyncio
    async def test_get_sell_price_level_1(self):
        """Тест цены продажи дрона 1 уровня (30%)"""
        price = DroneSystem.get_sell_price('basic', 1)
        # 7500 * 0.3 = 2250
        assert price['metal'] == 2250
        assert price['crystals'] == 0
        assert price['dark_matter'] == 0
    
    @pytest.mark.asyncio
    async def test_get_sell_price_level_2(self):
        """Тест цены продажи дрона 2 уровня (30% от 5 * цена 1 уровня)"""
        price = DroneSystem.get_sell_price('basic', 2)
        # 7500 * 5 * 0.3 = 11250
        assert price['metal'] == 11250
        assert price['crystals'] == 0
        assert price['dark_matter'] == 0
    
    @pytest.mark.asyncio
    async def test_get_sell_price_level_5(self):
        """Тест цены продажи дрона 5 уровня (30% от 625 * цена 1 уровня)"""
        price = DroneSystem.get_sell_price('basic', 5)
        # 7500 * 625 * 0.3 = 1406250
        assert price['metal'] == 1406250
        assert price['crystals'] == 0
        assert price['dark_matter'] == 0

    def test_get_sell_price_level_1(self):
        """Тест цены продажи дрона 1 уровня"""
        price = DroneSystem.get_sell_price('basic', 1)

        # 30% от 7500 = 2250
        assert price['metal'] == 2250
    
    def test_get_sell_price_level_2(self):
        """Тест цены продажи дрона 2 уровня"""
        price = DroneSystem.get_sell_price('basic', 2)
        
        # 5 дронов 1 уровня * 7500 * 0.3 = 11250
        assert price['metal'] == 11250
    
    def test_get_sell_price_level_5(self):
        """Тест цены продажи дрона 5 уровня"""
        price = DroneSystem.get_sell_price('basic', 5)
        
        # 625 дронов 1 уровня * 7500 * 0.3 = 1406250
        assert price['metal'] == 1406250


class TestDroneSystemCounting:
    """Тесты подсчёта дронов"""
    
    def test_calculate_total_drones_empty(self):
        """Тест подсчёта без дронов"""
        total = DroneSystem.calculate_total_drones({})
        assert total == 0
    
    def test_calculate_total_drones_single(self):
        """Тест подсчёта одного дрона"""
        drones_data = {'basic_lvl1': 5}
        total = DroneSystem.calculate_total_drones(drones_data)
        assert total == 5
    
    def test_calculate_total_drones_mixed(self):
        """Тест подсчёта смешанных дронов"""
        drones_data = {
            'basic_lvl1': 10,
            'basic_lvl2': 2,
            'miner_lvl1': 5,
            'ai_lvl5': 1
        }
        total = DroneSystem.calculate_total_drones(drones_data)
        assert total == 18


class TestDroneSystemUpgrade:
    """Тесты улучшения дронов"""
    
    def test_can_upgrade_success(self):
        """Тест возможности улучшения"""
        drones_data = {'basic_lvl1': 10}
        
        can, error = DroneSystem.can_upgrade(drones_data, 'basic', 1, 1)
        assert can is True
        assert error == ""
    
    def test_can_upgrade_not_enough(self):
        """Тест недостаточно дронов для улучшения"""
        drones_data = {'basic_lvl1': 3}
        
        can, error = DroneSystem.can_upgrade(drones_data, 'basic', 1, 1)
        assert can is False
        assert "Недостаточно" in error
    
    def test_can_upgrade_max_level(self):
        """Тест максимального уровня"""
        drones_data = {'basic_lvl5': 10}
        
        can, error = DroneSystem.can_upgrade(drones_data, 'basic', 5, 1)
        assert can is False
        assert "максимальный" in error.lower()
    
    def test_calculate_max_upgrades(self):
        """Тест расчёта максимального количества улучшений"""
        assert DroneSystem.calculate_max_upgrades(0) == 0
        assert DroneSystem.calculate_max_upgrades(4) == 0
        assert DroneSystem.calculate_max_upgrades(5) == 1
        assert DroneSystem.calculate_max_upgrades(10) == 2
        assert DroneSystem.calculate_max_upgrades(25) == 5


class TestDroneSystemHire:
    """Тесты найма дронов"""
    
    def test_can_hire_success(self):
        """Тест возможности найма"""
        drones_data = {'basic_lvl1': 10}
        
        can, error = DroneSystem.can_hire(drones_data, 0, 'basic', 1, 5)
        assert can is True
        assert error == ""
    
    def test_can_hire_limit_reached(self):
        """Тест достижения лимита найма"""
        drones_data = {'basic_lvl1': 10}
        
        can, error = DroneSystem.can_hire(drones_data, 50, 'basic', 1, 1)
        assert can is False
        assert "лимит" in error.lower()
    
    def test_can_hire_not_enough_drones(self):
        """Тест недостаточно дронов для найма"""
        drones_data = {'basic_lvl1': 2}
        
        can, error = DroneSystem.can_hire(drones_data, 0, 'basic', 1, 5)
        assert can is False
        assert "Недостаточно" in error
    
    def test_can_hire_not_enough_slots(self):
        """Тест недостаточно слотов для найма"""
        drones_data = {'basic_lvl1': 20}
        
        can, error = DroneSystem.can_hire(drones_data, 45, 'basic', 1, 10)
        assert can is False
        assert "слотов" in error.lower()


class TestDroneSystemStorage:
    """Тесты хранилища дронов"""
    
    def test_calculate_storage_income_no_hired(self):
        """Тест дохода без нанятых дронов"""
        now = datetime.now()
        last_update = now - timedelta(minutes=10)
        
        result = DroneSystem.calculate_storage_income({}, 0, last_update, now)
        
        assert result['metal'] == 0
        assert result['crystals'] == 0
        assert result['dark_matter'] == 0
    
    def test_calculate_storage_income_with_hired(self):
        """Тест накопленного дохода"""
        now = datetime.now()
        last_update = now - timedelta(minutes=10)
        
        drones_data = {'basic_lvl1': 5}
        
        result = DroneSystem.calculate_storage_income(drones_data, 5, last_update, now)
        
        # 5 дронов * 30 металла/мин * 10 минут = 1500
        assert result['metal'] == 1500
        assert result['minutes_passed'] == 10
    
    def test_check_mission_status_active(self):
        """Тест активной миссии"""
        now = datetime.now()
        hired_until = now + timedelta(hours=1)
        
        status = DroneSystem.check_mission_status(hired_until, now)
        
        assert status['is_active'] is True
        assert status['is_expired'] is False
    
    def test_check_mission_status_expired(self):
        """Тест завершённой миссии"""
        now = datetime.now()
        hired_until = now - timedelta(hours=1)
        
        status = DroneSystem.check_mission_status(hired_until, now)
        
        assert status['is_active'] is False
        assert status['is_expired'] is True
    
    def test_should_clear_storage_under_24h(self):
        """Тест: не очищать если меньше 24 часов"""
        now = datetime.now()
        hired_until = now - timedelta(hours=12)
        
        should_clear = DroneSystem.should_clear_storage(hired_until, now)
        
        assert should_clear is False
    
    def test_should_clear_storage_over_24h(self):
        """Тест: очистить если больше 24 часов"""
        now = datetime.now()
        hired_until = now - timedelta(hours=25)
        
        should_clear = DroneSystem.should_clear_storage(hired_until, now)
        
        assert should_clear is True


class TestDroneSystemFormatting:
    """Тесты форматирования"""
    
    def test_format_income_metal(self):
        """Тест форматирования дохода металла"""
        income = {'metal': 1000, 'crystals': 0, 'dark_matter': 0}
        
        result = DroneSystem.format_income(income)
        
        assert "⚙️" in result
        assert "1,000" in result
    
    def test_format_income_all(self):
        """Тест форматирования дохода всех ресурсов"""
        income = {'metal': 100, 'crystals': 50, 'dark_matter': 10}
        
        result = DroneSystem.format_income(income)
        
        assert "⚙️" in result
        assert "💎" in result
        assert "🕳️" in result
    
    def test_format_price_single(self):
        """Тест форматирования цены"""
        price = {'metal': 7500, 'crystals': 0, 'dark_matter': 0}
        
        result = DroneSystem.format_price(price)
        
        assert "7,500" in result
        assert "⚙️" in result
    
    def test_format_price_multiple(self):
        """Тест форматирования цены из нескольких ресурсов"""
        price = {'metal': 10000, 'crystals': 7500, 'dark_matter': 0}
        
        result = DroneSystem.format_price(price)
        
        assert "10,000" in result
        assert "7,500" in result


class TestDroneConstants:
    """Тесты констант системы дронов"""
    
    @pytest.mark.asyncio
    async def test_max_drone_level(self):
        """Тест максимального уровня"""
        from game.drones import MAX_DRONE_LEVEL
        assert MAX_DRONE_LEVEL == 5
    
    @pytest.mark.asyncio
    async def test_max_hired_drones(self):
        """Тест лимита найма"""
        from game.drones import MAX_HIRED_DRONES
        assert MAX_HIRED_DRONES == 50
    
    @pytest.mark.asyncio
    async def test_mission_duration(self):
        """Тест длительности миссии"""
        from game.drones import MISSION_DURATION_MINUTES
        assert MISSION_DURATION_MINUTES == 120


class TestDroneMission:
    """Тесты миссий дронов"""
    
    @pytest.mark.asyncio
    async def test_mission_duration_2_hours(self):
        """Тест длительности миссии 2 часа"""
        from game.drones import MISSION_DURATION_MINUTES
        assert MISSION_DURATION_MINUTES == 120
    
    @pytest.mark.asyncio
    async def test_storage_expire_24_hours(self):
        """Тест времени сгорания ресурсов 24 часа"""
        from game.drones import STORAGE_EXPIRE_MINUTES
        assert STORAGE_EXPIRE_MINUTES == 1440
    
    @pytest.mark.asyncio
    async def test_income_accumulation(self):
        """Тест накопления дохода"""
        from datetime import datetime, timedelta
        from game.drones import DroneSystem
        
        # 10 базовых дронов 1 уровня в найме
        drones_data = {'basic_lvl1': 10}
        hired_count = 10
        last_update = datetime.now() - timedelta(minutes=60)
        
        result = DroneSystem.calculate_storage_income(drones_data, hired_count, last_update)
        
        # 10 дронов × 30 металла/мин × 60 минут = 18000
        assert result['metal'] == 18000
        assert result['minutes_passed'] == 60
    
    @pytest.mark.asyncio
    async def test_income_accumulation_mission_ended(self):
        """Тест накопления дохода после окончания миссии"""
        from datetime import datetime, timedelta
        from game.drones import DroneSystem
        
        # Миссия закончилась 30 минут назад
        hired_until = datetime.now() - timedelta(minutes=30)
        now = datetime.now()
        
        status = DroneSystem.check_mission_status(hired_until, now)
        
        assert status['is_expired'] is True
        assert status['expired_hours_ago'] > 0
    
    @pytest.mark.asyncio
    async def test_resources_clear_after_24h(self):
        """Тест сгорания ресурсов через 24 часа"""
        from datetime import datetime, timedelta
        from game.drones import DroneSystem
        
        # Миссия закончилась 25 часов назад
        hired_until = datetime.now() - timedelta(hours=25)
        
        should_clear = DroneSystem.should_clear_storage(hired_until)
        
        assert should_clear is True
    
    @pytest.mark.asyncio
    async def test_resources_not_clear_under_24h(self):
        """Тест что ресурсы не сгорают раньше 24 часов"""
        from datetime import datetime, timedelta
        from game.drones import DroneSystem
        
        # Миссия закончилась 10 часов назад
        hired_until = datetime.now() - timedelta(hours=10)
        
        should_clear = DroneSystem.should_clear_storage(hired_until)
        
        assert should_clear is False
