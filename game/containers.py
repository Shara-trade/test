"""
Система контейнеров
Согласно Update.txt - 5 типов контейнеров с системой дропа материалов
"""
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ContainerType(Enum):
    COMMON = 'common'        # Обычный
    RARE = 'rare'            # Редкий
    EPIC = 'epic'            # Эпический
    MYTHIC = 'mythic'        # Мифический
    LEGENDARY = 'legendary'  # Легендарный
    KSM = 'ksm'              # Контейнер с модулями


@dataclass
class ContainerInfo:
    """Информация о типе контейнера"""
    container_type: ContainerType
    name: str
    emoji: str
    drop_chance: float  # Шанс выпадения при клике
    
    # Гарантированные ресурсы
    metal_min: int
    metal_max: int
    crystals_min: int
    crystals_max: int
    dark_matter_min: int
    dark_matter_max: int

    # Время разблокировки (в минутах)
    unlock_minutes: int = 5


class ContainerSystem:
    """Система контейнеров с предрасчитанными пулами материалов"""

    BASE_DROP_CHANCE = 0.01  # 1% шанс выпадения контейнера за клик
    MAX_CONTAINERS = 10  # Максимум контейнеров у игрока

    # Информация о типах контейнеров (согласно Update.txt)
    CONTAINER_INFO = {
        ContainerType.COMMON: ContainerInfo(
            container_type=ContainerType.COMMON,
            name="Обычный",
            emoji="📦",
            drop_chance=0.65,  # 65% от всех контейнеров
            metal_min=50, metal_max=100,
            crystals_min=10, crystals_max=25,
            dark_matter_min=0, dark_matter_max=5,
            unlock_minutes=5,
        ),
        ContainerType.RARE: ContainerInfo(
            container_type=ContainerType.RARE,
            name="Редкий",
            emoji="🎁",
            drop_chance=0.20,  # 20% от всех контейнеров
            metal_min=150, metal_max=300,
            crystals_min=40, crystals_max=80,
            dark_matter_min=10, dark_matter_max=25,
            unlock_minutes=15,
        ),
        ContainerType.EPIC: ContainerInfo(
            container_type=ContainerType.EPIC,
            name="Эпический",
            emoji="💎",
            drop_chance=0.09,  # 9% от всех контейнеров
            metal_min=400, metal_max=800,
            crystals_min=120, crystals_max=250,
            dark_matter_min=40, dark_matter_max=80,
            unlock_minutes=30,
        ),
        ContainerType.MYTHIC: ContainerInfo(
            container_type=ContainerType.MYTHIC,
            name="Мифический",
            emoji="👑",
            drop_chance=0.04,  # 4% от всех контейнеров
            metal_min=900, metal_max=1800,
            crystals_min=300, crystals_max=600,
            dark_matter_min=120, dark_matter_max=250,
            unlock_minutes=60,
        ),
        ContainerType.LEGENDARY: ContainerInfo(
            container_type=ContainerType.LEGENDARY,
            name="Легендарный",
            emoji="🔥",
            drop_chance=0.02,  # 2% от всех контейнеров
            metal_min=2000, metal_max=5000,
            crystals_min=800, crystals_max=2000,
            dark_matter_min=300, dark_matter_max=800,
            unlock_minutes=120,
        ),
        ContainerType.KSM: ContainerInfo(
            container_type=ContainerType.KSM,
            name="Контейнер с модулями",
            emoji="⚙️",
            drop_chance=0.0,  # Не выпадает при клике
            metal_min=0, metal_max=0,
            crystals_min=0, crystals_max=0,
            dark_matter_min=0, dark_matter_max=0,
            unlock_minutes=30,
        ),
    }

    # Названия для отображения
    CONTAINER_NAMES = {
        "common": "📦 Обычный",
        "rare": "🎁 Редкий",
        "epic": "💎 Эпический",
        "mythic": "👑 Мифический",
        "legendary": "🔥 Легендарный",
        "ksm": "⚙️ КСМ",
    }

    # Сокращения для команд
    CONTAINER_ALIASES = {
        # Полные названия
        "обычный": "common",
        "редкий": "rare",
        "эпический": "epic",
        "мифический": "mythic",
        "легендарный": "legendary",
        "ксм": "ksm",
        "контейнер с модулями": "ksm",
        # Сокращения
        "обы": "common",
        "ред": "rare",
        "эп": "epic",
        "миф": "mythic",
        "лег": "legendary",
        # Английские
        "common": "common",
        "rare": "rare",
        "epic": "epic",
        "mythic": "mythic",
        "legendary": "legendary",
        "ksm": "ksm",
    }

    # Предрасчитанные пулы материалов для каждого типа контейнера
    # Формат: {container_type: [(material, drop_chance, (min_amt, max_amt)), ...]}
    _material_pools: Dict[str, List[Tuple]] = {}
    _pools_initialized: bool = False

    @classmethod
    def _init_material_pools(cls):
        """Предрасчитать пулы материалов для каждого типа контейнера"""
        if cls._pools_initialized:
            return
        
        from game.materials import MaterialSystem
        
        for container_type in ['common', 'rare', 'epic', 'mythic', 'legendary']:
            pool = []
            for material in MaterialSystem.get_all_materials():
                drop_chance = material.drop_chances.get(container_type, 0)
                drop_amount = material.drop_amounts.get(container_type, (0, 0))
                
                if drop_chance > 0 and drop_amount[1] > 0:
                    pool.append((material, drop_chance, drop_amount))
            
            cls._material_pools[container_type] = pool
        
        cls._pools_initialized = True

    @staticmethod
    def try_drop_container() -> Optional[ContainerInfo]:
        """
        Попытка выпадения контейнера при клике.
        
        Returns:
            ContainerInfo или None
        """
        if random.random() > ContainerSystem.BASE_DROP_CHANCE:
            return None

        roll = random.random()
        cumulative = 0
        
        for container_info in ContainerSystem.CONTAINER_INFO.values():
            cumulative += container_info.drop_chance
            if roll <= cumulative:
                return container_info
        
        return ContainerSystem.CONTAINER_INFO[ContainerType.COMMON]

    @classmethod
    def generate_rewards(cls, container_type: str) -> Dict:
        """
        Сгенерировать награды за открытие контейнера.
        Согласно таблице шансов из Update.txt.
        Использует предрасчитанные пулы материалов для оптимизации.
        
        Args:
            container_type: Тип контейнера (common, rare, epic, mythic, legendary, ksm)
        
        Returns:
            Dict с ключами: container_type, resources, materials, module
        """
        # Инициализируем пулы если нужно
        cls._init_material_pools()
        
        container_info = cls.CONTAINER_INFO.get(ContainerType(container_type))
        if not container_info:
            return {"container_type": container_type, "resources": {}, "materials": {}}
        
        resources = {}
        materials = {}
        
        # ===== КСМ - генерируем модуль =====
        if container_type == 'ksm':
            from game.modules import ModuleSystem
            
            module = ModuleSystem.generate_module()
            return {
                "container_type": container_type,
                "resources": {},
                "materials": {},
                "module": module,
            }
        
        # ===== ГАРАНТИРОВАННЫЕ РЕСУРСЫ =====
        
        resources["metal"] = random.randint(container_info.metal_min, container_info.metal_max)
        resources["crystals"] = random.randint(container_info.crystals_min, container_info.crystals_max)
        resources["dark_matter"] = random.randint(container_info.dark_matter_min, container_info.dark_matter_max)
        
        # ===== МАТЕРИАЛЫ ИЗ ПРЕДРАСЧИТАННОГО ПУЛА =====
        
        pool = cls._material_pools.get(container_type, [])
        
        for material, drop_chance, drop_amount in pool:
            if random.random() < drop_chance:
                min_amt, max_amt = drop_amount
                amount = random.randint(min_amt, max_amt)
                if amount > 0:
                    materials[material.key] = amount
        
        return {
            "container_type": container_type,
            "resources": resources,
            "materials": materials,
        }

    @staticmethod
    def format_container_drop(container_info: ContainerInfo) -> str:
        """Форматировать сообщение о выпавшем контейнере"""
        return f"🎁 Найден {container_info.emoji} {container_info.name} контейнер!"

    @staticmethod
    def can_receive_container(current_count: int) -> bool:
        """Проверка, можно ли получить еще контейнер"""
        return current_count < ContainerSystem.MAX_CONTAINERS

    @staticmethod
    def get_container_by_type(container_type: str) -> Optional[ContainerInfo]:
        """Получить информацию о контейнере по типу"""
        try:
            ct = ContainerType(container_type)
            return ContainerSystem.CONTAINER_INFO.get(ct)
        except ValueError:
            return None

    @staticmethod
    def resolve_container_type(text: str) -> Optional[str]:
        """
        Определить тип контейнера из текста команды.

        Args:
            text: Текст от пользователя (например: "редкий", "ред", "rare")
        
        Returns:
            Тип контейнера или None
        """
        text_lower = text.lower().strip()
        return ContainerSystem.CONTAINER_ALIASES.get(text_lower)

    @staticmethod
    def get_container_name(container_type: str) -> str:
        """Получить отображаемое имя контейнера"""
        return ContainerSystem.CONTAINER_NAMES.get(container_type, "📦 Контейнер")


# Глобальный экземпляр
container_system = ContainerSystem()


