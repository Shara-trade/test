"""
Тесты системы дронов.
"""
import pytest
from game.drones import Drone, DroneSystem


class TestDrone:
    """Тесты дрона"""
    
    def test_drone_types(self):
        """Тест типов дронов"""
        assert 'basic' in Drone.DRONE_TYPES
        assert 'miner' in Drone.DRONE_TYPES
        assert 'laser' in Drone.DRONE_TYPES
        assert 'quantum' in Drone.DRONE_TYPES
        assert 'ai' in Drone.DRONE_TYPES
    
    def test_drone_info(self):
        """Тест информации о дроне"""
        info = Drone.get_drone_info('basic')
        
        assert info is not None
        assert info['name'] == 'Базовый дрон'
        assert info['base_income'] == 2
        assert info['slots'] == 1
    
    def test_drone_info_invalid(self):
        """Тест информации о несуществующем дроне"""
        info = Drone.get_drone_info('invalid')
        
        assert info is None
    
    def test_calculate_income(self):
        """Тест расчёта дохода"""
        # Базовый дрон 1 уровня
        income = Drone.calculate_income('basic', 1)
        assert income == 2  # base_income
        
        # Базовый дрон 2 уровня (+50%)
        income = Drone.calculate_income('basic', 2)
        assert income == 3  # 2 * 1.5 = 3
        
        # Базовый дрон 10 уровня
        income = Drone.calculate_income('basic', 10)
        assert income == 11  # 2 * (1 + 9 * 0.5) = 2 * 5.5 = 11
    
    def test_get_upgrade_cost(self):
        """Тест стоимости улучшения"""
        cost = Drone.get_upgrade_cost('basic', 1)
        
        assert 'metal' in cost
        assert 'crystals' in cost
        assert cost['metal'] > 0
    
    def test_income_scales_with_level(self):
        """Тест масштабирования дохода с уровнем"""
        incomes = [Drone.calculate_income('basic', level) for level in range(1, 11)]
        
        # Доход должен расти
        for i in range(1, len(incomes)):
            assert incomes[i] > incomes[i-1]
    
    def test_higher_tier_more_income(self):
        """Тест: дроны выше уровня дают больше дохода"""
        basic_income = Drone.calculate_income('basic', 1)
        miner_income = Drone.calculate_income('miner', 1)
        laser_income = Drone.calculate_income('laser', 1)
        quantum_income = Drone.calculate_income('quantum', 1)
        ai_income = Drone.calculate_income('ai', 1)
        
        assert basic_income < miner_income
        assert miner_income < laser_income
        assert laser_income < quantum_income
        assert quantum_income < ai_income


class TestDroneSystem:
    """Тесты системы дронов"""
    
    def test_calculate_total_income(self):
        """Тест расчёта общего дохода"""
        drones = [
            Drone(id=1, user_id=1, drone_type='basic', level=1, income_per_tick=2),
            Drone(id=2, user_id=1, drone_type='miner', level=1, income_per_tick=8),
        ]
        
        total = DroneSystem.calculate_total_income(drones)
        assert total == 10
    
    def test_calculate_total_income_empty(self):
        """Тест расчёта дохода без дронов"""
        total = DroneSystem.calculate_total_income([])
        assert total == 0
    
    def test_calculate_total_income_inactive(self):
        """Тест расчёта дохода с неактивными дронами"""
        drones = [
            Drone(id=1, user_id=1, drone_type='basic', level=1, income_per_tick=2, is_active=True),
            Drone(id=2, user_id=1, drone_type='miner', level=1, income_per_tick=8, is_active=False),
        ]
        
        total = DroneSystem.calculate_total_income(drones)
        assert total == 2  # Только активный
    
    def test_calculate_income_with_synergy(self):
        """Тест расчёта дохода с синергией"""
        drones = [
            Drone(id=1, user_id=1, drone_type='basic', level=1, income_per_tick=2),
            Drone(id=2, user_id=1, drone_type='basic', level=1, income_per_tick=2),
            Drone(id=3, user_id=1, drone_type='miner', level=1, income_per_tick=8),
        ]
        
        result = DroneSystem.calculate_income_with_synergy(drones)
        
        assert 'base_income' in result
        assert 'count_bonus' in result
        assert 'variety_bonus' in result
        assert 'total_multiplier' in result
        assert 'final_income' in result
        
        # Базовый доход = 2 + 2 + 8 = 12
        assert result['base_income'] == 12
        
        # Финальный доход должен быть больше базового (бонусы)
        assert result['final_income'] > result['base_income']
    
    def test_synergy_count_bonus(self):
        """Тест бонуса за количество"""
        # Создаём 10 дронов
        drones = [
            Drone(id=i, user_id=1, drone_type='basic', level=1, income_per_tick=2)
            for i in range(10)
        ]
        
        result = DroneSystem.calculate_income_with_synergy(drones)
        
        # 10 дронов = +50% бонус за количество
        assert result['count_bonus'] == 1.5  # 1 + 10 * 0.05
    
    def test_synergy_variety_bonus(self):
        """Тест бонуса за разнообразие"""
        drones = [
            Drone(id=1, user_id=1, drone_type='basic', level=1, income_per_tick=2),
            Drone(id=2, user_id=1, drone_type='miner', level=1, income_per_tick=8),
            Drone(id=3, user_id=1, drone_type='laser', level=1, income_per_tick=25),
        ]
        
        result = DroneSystem.calculate_income_with_synergy(drones)
        
        # 3 уникальных типа = +30% бонус
        assert result['variety_bonus'] == 1.3  # 1 + 3 * 0.10
    
    def test_synergy_level_bonus(self):
        """Тест бонуса за уровень"""
        drones = [
            Drone(id=1, user_id=1, drone_type='basic', level=6, income_per_tick=5),  # > 5
            Drone(id=2, user_id=1, drone_type='basic', level=7, income_per_tick=6),  # > 5
            Drone(id=3, user_id=1, drone_type='basic', level=3, income_per_tick=3),  # <= 5
        ]
        
        result = DroneSystem.calculate_income_with_synergy(drones)
        
        # 2 дрона с уровнем > 5 = +4% бонус
        assert result['level_bonus'] == 1.04  # 1 + 2 * 0.02
    
    def test_calculate_offline_income(self):
        """Тест расчёта оффлайн дохода"""
        drones = [
            Drone(id=1, user_id=1, drone_type='basic', level=1, income_per_tick=2),
        ]
        
        result = DroneSystem.calculate_offline_income(drones, minutes_offline=60)
        
        assert 'metal' in result
        assert 'crystals' in result
        assert 'ticks' in result
        
        # 60 минут = 720 тиков (60 * 60 / 5)
        assert result['ticks'] == 720
    
    def test_offline_income_max_24_hours(self):
        """Тест лимита оффлайн дохода в 24 часа"""
        drones = [
            Drone(id=1, user_id=1, drone_type='basic', level=1, income_per_tick=2),
        ]
        
        # 48 часов
        result_48h = DroneSystem.calculate_offline_income(drones, minutes_offline=48 * 60)
        
        # 24 часа
        result_24h = DroneSystem.calculate_offline_income(drones, minutes_offline=24 * 60)
        
        # Должны быть одинаковыми (лимит 24 часа)
        assert result_48h['metal'] == result_24h['metal']
    
    def test_can_buy_drone(self):
        """Тест проверки покупки дрона"""
        assert DroneSystem.can_buy_drone(0) is True
        assert DroneSystem.can_buy_drone(49) is True
        assert DroneSystem.can_buy_drone(50) is False
    
    def test_can_upgrade_drone(self):
        """Тест проверки улучшения дрона"""
        drone_max_level = Drone(id=1, user_id=1, drone_type='basic', level=10)
        drone_low_level = Drone(id=2, user_id=1, drone_type='basic', level=5)
        
        assert DroneSystem.can_upgrade_drone(drone_max_level) is False
        assert DroneSystem.can_upgrade_drone(drone_low_level) is True
    
    def test_get_synergy_description(self):
        """Тест описания синергии"""
        drones = [
            Drone(id=1, user_id=1, drone_type='basic', level=1, income_per_tick=2),
            Drone(id=2, user_id=1, drone_type='miner', level=1, income_per_tick=8),
        ]
        
        description = DroneSystem.get_synergy_description(drones)
        
        assert isinstance(description, str)
        assert len(description) > 0

    def test_synergy_empty_drones(self):
        """Тест синергии без дронов"""
        result = DroneSystem.calculate_income_with_synergy([])
        
        assert result['base_income'] == 0
        assert result['final_income'] == 0
    
    def test_synergy_all_inactive(self):
        """Тест синергии со всеми неактивными дронами"""
        drones = [
            Drone(id=1, user_id=1, drone_type='basic', level=1, income_per_tick=2, is_active=False),
        ]
        
        result = DroneSystem.calculate_income_with_synergy(drones)
        
        assert result['base_income'] == 0
        assert result['final_income'] == 0
