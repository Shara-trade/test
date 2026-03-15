"""
Тесты системы модулей.
"""
import pytest
from game.modules import (
    ModuleSystem, Rarity, RARITY_EMOJI, RARITY_NAME,
    BUFF_NAMES, DEBUFF_NAMES, BUFF_KEYS, DEBUFF_KEYS,
    BUFF_COUNT, DEBUFF_COUNT, BUFF_VALUES, DEBUFF_VALUES
)


class TestModuleSystem:
    """Тесты системы модулей"""
    
    def test_generate_module(self):
        """Тест генерации модуля"""
        module = ModuleSystem.generate_module()
        
        assert "name" in module
        assert "rarity" in module
        assert "buffs" in module
        assert "debuffs" in module
        
        assert isinstance(module["name"], str)
        assert len(module["name"]) > 0
        assert module["rarity"] in Rarity
        assert isinstance(module["buffs"], dict)
        assert isinstance(module["debuffs"], dict)
    
    def test_roll_rarity(self):
        """Тест определения редкости"""
        rarity = ModuleSystem.roll_rarity()
        
        assert rarity in Rarity
    
    def test_rarity_distribution(self):
        """Тест распределения редкости"""
        stats = {r: 0 for r in Rarity}
        
        for _ in range(1000):
            rarity = ModuleSystem.roll_rarity()
            stats[rarity] += 1
        
        # Обычных должно быть больше чем легендарных
        assert stats[Rarity.COMMON] > stats[Rarity.LEGENDARY]
    
    def test_generate_name(self):
        """Тест генерации имени"""
        for _ in range(100):
            name = ModuleSystem.generate_name()
            
            # Имя должно быть формата XX-NN
            assert len(name) >= 4
            assert "-" in name
    
    def test_select_effects(self):
        """Тест выбора эффектов"""
        count_range = (2, 4, 0.5)
        selected = ModuleSystem.select_effects(BUFF_KEYS, count_range)
        
        assert len(selected) >= 2
        assert len(selected) <= 4
        assert all(key in BUFF_KEYS for key in selected)
        
    def test_buffs_count_by_rarity(self):
        """Тест количества бафов по редкости"""
        for _ in range(10):  # Несколько попыток из-за случайности
            module = ModuleSystem.generate_module()
            rarity = module["rarity"]
            count_range = BUFF_COUNT[rarity]
            
            actual_count = len(module["buffs"])
            min_count, max_count, _ = count_range
            
            assert min_count <= actual_count <= max_count
    
    def test_debuffs_count_by_rarity(self):
        """Тест количества дебафов по редкости"""
        for _ in range(10):  # Несколько попыток из-за случайности
            module = ModuleSystem.generate_module()
            rarity = module["rarity"]
            count_range = DEBUFF_COUNT[rarity]
            
            actual_count = len(module["debuffs"])
            min_count, max_count, _ = count_range
            
            assert min_count <= actual_count <= max_count
    
    def test_buff_values_by_rarity(self):
        """Тест значений бафов по редкости"""
        for rarity in Rarity:
            module = ModuleSystem.generate_module()
            # Форсируем редкость через генерацию
            
            for buff_key, value in module["buffs"].items():
                expected_value = BUFF_VALUES[buff_key][module["rarity"]]
                assert value == expected_value
    
    def test_legendary_has_more_buffs_than_common(self):
        """Тест: легендарный модуль имеет больше бафов чем обычный"""
        # Генерируем много модулей и ищем нужные редкости
        common_buffs = 0
        legendary_buffs = 0
        
        for _ in range(1000):
            module = ModuleSystem.generate_module()
            if module["rarity"] == Rarity.COMMON:
                common_buffs = len(module["buffs"])
            elif module["rarity"] == Rarity.LEGENDARY:
                legendary_buffs = len(module["buffs"])
            
            if common_buffs > 0 and legendary_buffs > 0:
                break
        
        assert legendary_buffs >= common_buffs
    
    def test_upgrade_module(self):
        """Тест улучшения модуля"""
        buffs = {"asteroid_resources": 5.5}
        debuffs = {"resource_reduction": 11.0}
        
        result = ModuleSystem.upgrade_module(buffs, debuffs, Rarity.COMMON)
        
        assert result is not None
        assert result["rarity"] == Rarity.RARE
        assert "asteroid_resources" in result["buffs"]
    
    def test_upgrade_module_max_rarity(self):
        """Тест улучшения максимальной редкости"""
        buffs = {}
        debuffs = {}
        
        result = ModuleSystem.upgrade_module(buffs, debuffs, Rarity.LEGENDARY)
        
        assert result is None
    
    def test_get_upgrade_cost(self):
        """Тест стоимости улучшения"""
        cost = ModuleSystem.get_upgrade_cost(Rarity.COMMON)
        
        assert cost is not None
        assert "asteroid_rock" in cost
        assert "quantum_fragment" in cost
    
    def test_get_upgrade_cost_max_rarity(self):
        """Тест стоимости улучшения максимальной редкости"""
        cost = ModuleSystem.get_upgrade_cost(Rarity.LEGENDARY)
        
        assert cost is None
    
    def test_get_scrap_rewards(self):
        """Тест наград за разборку"""
        rewards = ModuleSystem.get_scrap_rewards(Rarity.COMMON)
        
        assert "asteroid_rock" in rewards
        assert "chance" in rewards
    
    def test_get_sell_price(self):
        """Тест цены продажи"""
        price_common = ModuleSystem.get_sell_price(Rarity.COMMON)
        price_legendary = ModuleSystem.get_sell_price(Rarity.LEGENDARY)
        
        assert price_common == 500
        assert price_legendary == 15000
        assert price_legendary > price_common
    
    def test_format_buff(self):
        """Тест форматирования бафа"""
        text = ModuleSystem.format_buff("asteroid_resources", 5.5)
        
        assert "Ресурсы" in text
        assert "5.5" in text
    
    def test_format_debuff(self):
        """Тест форматирования дебафа"""
        text = ModuleSystem.format_debuff("resource_reduction", 11.0)
        
        assert "Снижение" in text
        assert "11.0" in text
    
    def test_format_module_card(self):
        """Тест форматирования карточки модуля"""
        module = {
            "module_id": 123,
            "name": "AB-42",
            "rarity": Rarity.RARE,
            "buffs": {"asteroid_resources": 7.5},
            "debuffs": {"resource_reduction": 8.5},
            "slot": "head"
        }
        
        text = ModuleSystem.format_module_card(module)
        
        assert "AB-42" in text
        assert "Редкая" in text
        assert "head" in text


class TestRaritySystem:
    """Тесты системы редкости"""
    
    def test_rarity_order(self):
        """Тест порядка редкости"""
        assert Rarity.COMMON < Rarity.RARE
        assert Rarity.RARE < Rarity.EPIC
        assert Rarity.EPIC < Rarity.MYTHIC
        assert Rarity.MYTHIC < Rarity.LEGENDARY
    
    def test_rarity_emoji(self):
        """Тест эмодзи редкости"""
        assert RARITY_EMOJI[Rarity.COMMON] == "⚪"
        assert RARITY_EMOJI[Rarity.RARE] == "🟢"
        assert RARITY_EMOJI[Rarity.EPIC] == "🟣"
        assert RARITY_EMOJI[Rarity.MYTHIC] == "🔴"
        assert RARITY_EMOJI[Rarity.LEGENDARY] == "🟡"
    
    def test_rarity_names(self):
        """Тест названий редкости"""
        assert RARITY_NAME[Rarity.COMMON] == "Обычная"
        assert RARITY_NAME[Rarity.RARE] == "Редкая"
        assert RARITY_NAME[Rarity.EPIC] == "Эпическая"
        assert RARITY_NAME[Rarity.MYTHIC] == "Мифическая"
        assert RARITY_NAME[Rarity.LEGENDARY] == "Легендарная"
