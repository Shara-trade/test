"""
Тесты механики добычи.
"""
import pytest
from game.mining import MiningSystem


class TestMiningSystem:
    """Тесты системы добычи"""
    
    def test_calculate_mining_basic(self):
        """Тест базового расчёта добычи"""
        result = MiningSystem.calculate_mining(
            user_level=1,
            drone_power=0,
            modules_bonus=0,
            system_multiplier=1.0,
            heat_percent=0
        )
        
        assert "metal" in result
        assert "crystals" in result
        assert "dark_matter" in result
        
        assert result["metal"] > 0
        assert result["crystals"] >= 0
        assert result["dark_matter"] >= 0
    
    def test_calculate_mining_with_drone_power(self):
        """Тест расчёта с мощностью дронов"""
        result_no_drone = MiningSystem.calculate_mining(
            user_level=10,
            drone_power=0,
            modules_bonus=0
        )
        
        result_with_drone = MiningSystem.calculate_mining(
            user_level=10,
            drone_power=100,
            modules_bonus=0
        )
        
        # С дронами должно быть больше металла
        assert result_with_drone["metal"] > result_no_drone["metal"]
    
    def test_calculate_mining_with_modules(self):
        """Тест расчёта с бонусом модулей"""
        result_no_module = MiningSystem.calculate_mining(
            user_level=10,
            drone_power=0,
            modules_bonus=0
        )
        
        result_with_module = MiningSystem.calculate_mining(
            user_level=10,
            drone_power=0,
            modules_bonus=50
        )
        
        # С модулями должно быть больше
        assert result_with_module["metal"] > result_no_module["metal"]
    
    def test_calculate_mining_with_multiplier(self):
        """Тест расчёта с множителем"""
        result_normal = MiningSystem.calculate_mining(
            user_level=10,
            drone_power=0,
            modules_bonus=0,
            system_multiplier=1.0
        )
        
        result_boosted = MiningSystem.calculate_mining(
            user_level=10,
            drone_power=0,
            modules_bonus=0,
            system_multiplier=2.0
        )
        
        # С множителем 2x должно быть примерно в 2 раза больше
        ratio = result_boosted["metal"] / result_normal["metal"]
        assert 1.5 < ratio < 2.5

    def test_calculate_mining_with_heat(self):
        """Тест расчёта с нагревом"""
        result_no_heat = MiningSystem.calculate_mining(
            user_level=10,
            drone_power=0,
            modules_bonus=0,
            heat_percent=0
        )
        
        result_with_heat = MiningSystem.calculate_mining(
            user_level=10,
            drone_power=0,
            modules_bonus=0,
            heat_percent=50
        )
        
        # С нагревом должно быть больше (до 80%)
        assert result_with_heat["metal"] > result_no_heat["metal"]
    
    def test_heat_overheat(self):
        """Тест перегрева (>80% нагрева)"""
        result_normal = MiningSystem.calculate_mining(
            user_level=10,
            drone_power=0,
            modules_bonus=0,
            heat_percent=50
        )
        
        result_overheat = MiningSystem.calculate_mining(
            user_level=10,
            drone_power=0,
            modules_bonus=0,
            heat_percent=90
        )
        
        # При перегреве бонуса нет
        assert result_overheat["metal"] <= result_normal["metal"]
    
    def test_dark_matter_drop_rate(self):
        """Тест частоты выпадения тёмной материи"""
        dm_count = 0
        attempts = 1000
        
        for _ in range(attempts):
            result = MiningSystem.calculate_mining(
                user_level=10,
                drone_power=0,
                modules_bonus=0
            )
            if result["dark_matter"] > 0:
                dm_count += 1
        
        # Примерно 1% шанс
        drop_rate = dm_count / attempts
        assert 0.005 < drop_rate < 0.02
    
    def test_get_click_cost(self):
        """Тест стоимости клика"""
        cost = MiningSystem.get_click_cost()
        
        assert cost == 10
    
    def test_can_click_sufficient_energy(self):
        """Тест проверки энергии (достаточно)"""
        assert MiningSystem.can_click(100) is True
        assert MiningSystem.can_click(10) is True
    
    def test_can_click_insufficient_energy(self):
        """Тест проверки энергии (недостаточно)"""
        assert MiningSystem.can_click(9) is False
        assert MiningSystem.can_click(0) is False
    
    def test_crystal_ratio(self):
        """Тест соотношения кристаллов к металлу"""
        results = [
            MiningSystem.calculate_mining(user_level=10)
            for _ in range(100)
        ]
        
        total_metal = sum(r["metal"] for r in results)
        total_crystals = sum(r["crystals"] for r in results)
        
        # Кристаллы примерно 10% от металла
        if total_crystals > 0:
            ratio = total_crystals / total_metal
            assert 0.02 < ratio < 0.2
