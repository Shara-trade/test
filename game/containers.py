"""
3.11. Система контейнеров (таймеры)
"""
import random
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class ContainerType(Enum):
    COMMON = 'common'  # Обычный - 5 мин
    RARE = 'rare'  # Редкий - 15 мин
    EPIC = 'epic'  # Эпический - 60 мин
    LEGENDARY = 'legendary'  # Легендарный - 180 мин


@dataclass
class ContainerInfo:
    """Информация о типе контейнера"""
    container_type: ContainerType
    name: str
    emoji: str
    unlock_minutes: int
    drop_chance: float  # Шанс выпадения при клике
    metal_min: int
    metal_max: int
    crystals_min: int
    crystals_max: int
    dark_matter_chance: float
    dark_matter_min: int
    dark_matter_max: int
    item_drop_chance: Dict[str, float]  # редкость -> шанс


class ContainerSystem:
    """Система контейнеров"""

    BASE_DROP_CHANCE = 0.01  # 1% шанс выпадения контейнера за клик
    MAX_CONTAINERS = 10  # Максимум контейнеров в очереди

    # Информация о типах контейнеров
    CONTAINER_INFO = {
        ContainerType.COMMON: ContainerInfo(
            container_type=ContainerType.COMMON,
            name="Обычный",
            emoji="📦",
            unlock_minutes=5,
            drop_chance=0.70,  # 70% от всех контейнеров
            metal_min=50, metal_max=150,
            crystals_min=5, crystals_max=20,
            dark_matter_chance=0.0,
            dark_matter_min=0, dark_matter_max=0,
            item_drop_chance={'common': 0.60, 'rare': 0.30, 'epic': 0.10}
        ),
        ContainerType.RARE: ContainerInfo(
            container_type=ContainerType.RARE,
            name="Редкий",
            emoji="💎",
            unlock_minutes=15,
            drop_chance=0.20,  # 20% от всех контейнеров
            metal_min=200, metal_max=500,
            crystals_min=30, crystals_max=100,
            dark_matter_chance=0.05,
            dark_matter_min=1, dark_matter_max=3,
            item_drop_chance={'common': 0.30, 'rare': 0.45, 'epic': 0.20, 'legendary': 0.05}
        ),
        ContainerType.EPIC: ContainerInfo(
            container_type=ContainerType.EPIC,
            name="Эпический",
            emoji="💜",
            unlock_minutes=60,
            drop_chance=0.08,  # 8% от всех контейнеров
            metal_min=500, metal_max=1500,
            crystals_min=100, crystals_max=300,
            dark_matter_chance=0.15,
            dark_matter_min=3, dark_matter_max=10,
            item_drop_chance={'rare': 0.40, 'epic': 0.45, 'legendary': 0.15}
        ),
        ContainerType.LEGENDARY: ContainerInfo(
            container_type=ContainerType.LEGENDARY,
            name="Легендарный",
            emoji="💛",
            unlock_minutes=180,
            drop_chance=0.02,  # 2% от всех контейнеров
            metal_min=2000, metal_max=5000,
            crystals_min=500, crystals_max=1500,
            dark_matter_chance=0.30,
            dark_matter_min=10, dark_matter_max=30,
            item_drop_chance={'epic': 0.50, 'legendary': 0.50}
        ),
    }

    @staticmethod
    def try_drop_container() -> Optional[ContainerInfo]:
        """
        Попытка выпадения контейнера при клике.
        
        Returns:
            ContainerInfo или None
        """
        # Проверяем базовый шанс выпадения
        if random.random() > ContainerSystem.BASE_DROP_CHANCE:
            return None

        # Определяем тип контейнера
        roll = random.random()
        cumulative = 0
        
        for container_info in ContainerSystem.CONTAINER_INFO.values():
            cumulative += container_info.drop_chance
            if roll <= cumulative:
                return container_info
        
        return ContainerSystem.CONTAINER_INFO[ContainerType.COMMON]

    @staticmethod
    def generate_rewards(container_info: ContainerInfo) -> Dict:
        """Сгенерировать награды за открытие контейнера"""
        rewards = []
        
        # Металл
        metal = random.randint(container_info.metal_min, container_info.metal_max)
        rewards.append({
            "type": "resource",
            "resource": "metal",
            "quantity": metal
        })
        
        # Кристаллы
        crystals = random.randint(container_info.crystals_min, container_info.crystals_max)
        rewards.append({
            "type": "resource",
            "resource": "crystals",
            "quantity": crystals
        })
        
        # Тёмная материя
        if random.random() < container_info.dark_matter_chance:
            dark_matter = random.randint(container_info.dark_matter_min, container_info.dark_matter_max)
            rewards.append({
                "type": "resource",
                "resource": "dark_matter",
                "quantity": dark_matter
            })
        
        # Предметы
        item_drop = container_info.item_drop_chance
        if item_drop:
            # Определяем редкость предмета
            roll = random.random()
            cumulative = 0
            selected_rarity = 'common'
            
            for rarity, chance in item_drop.items():
                cumulative += chance
                if roll <= cumulative:
                    selected_rarity = rarity
                    break
            
            # Случайный предмет этой редкости
            item = ContainerSystem._get_random_item(selected_rarity)
            if item:
                rewards.append(item)
        
        return {
            "container": container_info,
            "rewards": rewards
        }

    @staticmethod
    def _get_random_item(rarity: str) -> Optional[Dict]:
        """Получить случайный предмет указанной редкости"""
        # Предметы по редкости
        items_by_rarity = {
            'common': [
                {'item_key': 'laser_mk1', 'name': 'Лазерный модуль Mk1', 'quantity': 1},
                {'item_key': 'battery_mk1', 'name': 'Батарея Mk1', 'quantity': 1},
                {'item_key': 'scanner_mk1', 'name': 'Сканер Mk1', 'quantity': 1},
            ],
            'rare': [
                {'item_key': 'laser_mk2', 'name': 'Лазерный модуль Mk2', 'quantity': 1},
                {'item_key': 'battery_mk2', 'name': 'Батарея Mk2', 'quantity': 1},
                {'item_key': 'turbine_mk1', 'name': 'Турбина Mk1', 'quantity': 1},
                {'item_key': 'ancient_engine', 'name': 'Древний двигатель', 'quantity': 1},
            ],
            'epic': [
                {'item_key': 'quantum_module', 'name': 'Квантовый модуль', 'quantity': 1},
                {'item_key': 'plasma_shield', 'name': 'Плазменный щит', 'quantity': 1},
                {'item_key': 'ai_core', 'name': 'Ядро ИИ', 'quantity': 1},
            ],
            'legendary': [
                {'item_key': 'alien_artifact', 'name': 'Инопланетный артефакт', 'quantity': 1},
            ]
        }
        
        items = items_by_rarity.get(rarity, [])
        if not items:
            return None

        item = random.choice(items)
        return {
            "type": "item",
            "item_key": item['item_key'],
            "name": item['name'],
            "quantity": item['quantity'],
            "rarity": rarity
        }

    @staticmethod
    def format_container_drop(container_info: ContainerInfo) -> str:
        """Форматировать сообщение о выпавшем контейнере"""
        return f"🎁 Найден {container_info.emoji} {container_info.name} контейнер! ({container_info.unlock_minutes} мин)"

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


# Глобальный экземпляр
container_system = ContainerSystem()

