"""
Тесты системы контейнеров.
"""
import pytest
from game.containers import ContainerSystem, ContainerType, ContainerInfo


class TestContainerSystem:
    """Тесты системы контейнеров"""
    
    def test_container_info(self):
        """Тест информации о контейнере"""
        info = ContainerSystem.CONTAINER_INFO[ContainerType.COMMON]
        
        assert info.name == "Обычный"
        assert info.emoji == "📦"
        assert info.metal_min < info.metal_max
        assert info.crystals_min < info.crystals_max
    
    def test_try_drop_container(self):
        """Тест выпадения контейнера"""
        # Проверяем, что метод работает
        dropped_count = 0
        
        for _ in range(1000):
            container = ContainerSystem.try_drop_container()
            if container:
                dropped_count += 1
        
        # Примерно 1% должны выпадать (BASE_DROP_CHANCE = 0.01)
        # При 1000 попыток ожидаем ~10 выпадений
        assert dropped_count > 0
    
    def test_generate_rewards_common(self):
        """Тест генерации наград обычного контейнера"""
        rewards = ContainerSystem.generate_rewards("common")
        
        assert "container_type" in rewards
        assert "resources" in rewards
        assert "materials" in rewards
        
        # Обычный контейнер должен давать металл
        assert rewards["resources"]["metal"] > 0
    
    def test_generate_rewards_legendary(self):
        """Тест генерации наград легендарного контейнера"""
        rewards = ContainerSystem.generate_rewards("legendary")
        
        # Легендарный должен давать больше ресурсов
        assert rewards["resources"]["metal"] >= 2000  # metal_min для legendary
    
    def test_generate_rewards_ksm(self):
        """Тест генерации наград КСМ"""
        rewards = ContainerSystem.generate_rewards("ksm")
        
        # КСМ должен давать модуль
        assert "module" in rewards
        assert rewards["module"] is not None
    
    def test_resource_ranges(self):
        """Тест границ ресурсов"""
        for container_type in [ContainerType.COMMON, ContainerType.RARE, 
                               ContainerType.EPIC, ContainerType.MYTHIC, 
                               ContainerType.LEGENDARY]:
            info = ContainerSystem.CONTAINER_INFO[container_type]
            
            # Генерируем несколько раз и проверяем границы
            for _ in range(50):
                rewards = ContainerSystem.generate_rewards(container_type.value)
                
                metal = rewards["resources"]["metal"]
                crystals = rewards["resources"]["crystals"]
                dark_matter = rewards["resources"]["dark_matter"]
                
                assert info.metal_min <= metal <= info.metal_max
                assert info.crystals_min <= crystals <= info.crystals_max
                assert info.dark_matter_min <= dark_matter <= info.dark_matter_max
    
    def test_can_receive_container(self):
        """Тест проверки лимита контейнеров"""
        # Можно получить если меньше 10
        assert ContainerSystem.can_receive_container(0) is True
        assert ContainerSystem.can_receive_container(9) is True
        
        # Нельзя если уже 10
        assert ContainerSystem.can_receive_container(10) is False
        assert ContainerSystem.can_receive_container(15) is False
    
    def test_resolve_container_type(self):
        """Тест определения типа контейнера из текста"""
        # Полные названия
        assert ContainerSystem.resolve_container_type("обычный") == "common"
        assert ContainerSystem.resolve_container_type("редкий") == "rare"
        assert ContainerSystem.resolve_container_type("эпический") == "epic"
        
        # Сокращения
        assert ContainerSystem.resolve_container_type("ред") == "rare"
        assert ContainerSystem.resolve_container_type("эп") == "epic"
        
        # Английские
        assert ContainerSystem.resolve_container_type("common") == "common"
        assert ContainerSystem.resolve_container_type("legendary") == "legendary"
        
        # Несуществующий
        assert ContainerSystem.resolve_container_type("invalid") is None
    
    def test_get_container_name(self):
        """Тест получения имени контейнера"""
        assert "Обычный" in ContainerSystem.get_container_name("common")
        assert "Редкий" in ContainerSystem.get_container_name("rare")
        assert "Легендарный" in ContainerSystem.get_container_name("legendary")

    def test_format_container_drop(self):
        """Тест форматирования сообщения о выпадении"""
        info = ContainerSystem.CONTAINER_INFO[ContainerType.RARE]
        text = ContainerSystem.format_container_drop(info)

        assert "🎁" in text
        assert "Редкий" in text


class TestContainerMaterialPools:
    """Тесты пулов материалов контейнеров"""
    
    def test_material_pools_initialization(self):
        """Тест инициализации пулов материалов"""
        # Инициализируем пулы
        ContainerSystem._init_material_pools()
        
        assert ContainerSystem._pools_initialized is True
    
    def test_get_container_by_type(self):
        """Тест получения контейнера по типу"""
        info = ContainerSystem.get_container_by_type("common")
        
        assert info is not None
        assert info.name == "Обычный"
        
        info = ContainerSystem.get_container_by_type("invalid")
        assert info is None
