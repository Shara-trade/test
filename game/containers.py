"""
3.11. Система контейнеров (таймеры)
"""
import random
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class ContainerType(Enum):
    COMMON = 'common'  # Обычный - 30 мин
    RARE = 'rare'  # Редкий - 2 часа
    EPIC = 'epic'  # Эпический - 6 часов
    LEGENDARY = 'legendary'  # Легендарный - 12 часов


@dataclass
class Container:
    """Модель контейнера"""
    id: int
    user_id: int
    container_type: ContainerType
    status: str  # 'locked', 'ready', 'opened'
    unlock_time: Optional[datetime] = None
    created_at: Optional[datetime] = None

    CONTAINER_SETTINGS = {
        ContainerType.COMMON: {
            'unlock_minutes': 30,
            'drop_chance': {'common': 0.70, 'rare': 0.25, 'epic': 0.05},
            'resources': {'min': 50, 'max': 200}
        },
        ContainerType.RARE: {
            'unlock_minutes': 120,
            'drop_chance': {'common': 0.40, 'rare': 0.40, 'epic': 0.15, 'legendary': 0.05},
            'resources': {'min': 200, 'max': 1000}
        },
        ContainerType.EPIC: {
            'unlock_minutes': 360,
            'drop_chance': {'rare': 0.50, 'epic': 0.35, 'legendary': 0.15},
            'resources': {'min': 1000, 'max': 5000}
        },
        ContainerType.LEGENDARY: {
            'unlock_minutes': 720,
            'drop_chance': {'epic': 0.60, 'legendary': 0.35, 'relic': 0.05},
            'resources': {'min': 5000, 'max': 20000}
        }
    }

    def get_unlock_time(self) -> Optional[datetime]:
        """Получить время открытия"""
        if self.created_at and self.status == 'locked':
            settings = self.CONTAINER_SETTINGS.get(self.container_type)
            if settings:
                return self.created_at + timedelta(minutes=settings['unlock_minutes'])
        return None

    def is_ready(self) -> bool:
        """Проверка, готов ли контейнер к открытию"""
        if self.status != 'locked':
            return self.status == 'ready'

        unlock_time = self.get_unlock_time()
        if unlock_time:
            return datetime.now() >= unlock_time
        return False

    def get_time_remaining(self) -> Optional[timedelta]:
        """Получить оставшееся время"""
        if self.status != 'locked':
            return None

        unlock_time = self.get_unlock_time()
        if unlock_time:
            remaining = unlock_time - datetime.now()
            return remaining if remaining.total_seconds() > 0 else timedelta(0)
        return None


class ContainerSystem:
    """Система контейнеров"""

    BASE_DROP_CHANCE = 0.02  # 2% шанс выпадения контейнера за клик
    MAX_CONTAINERS = 10  # Максимум контейнеров в очереди

    @staticmethod
    def try_drop_container() -> Optional[ContainerType]:
        """Попытка выпадения контейнера"""
        if random.random() > ContainerSystem.BASE_DROP_CHANCE:
            return None

        # Шансы типов контейнеров
        roll = random.random()
        if roll < 0.60:
            return ContainerType.COMMON
        elif roll < 0.85:
            return ContainerType.RARE
        elif roll < 0.95:
            return ContainerType.EPIC
        else:
            return ContainerType.LEGENDARY

    @staticmethod
    def open_container(container: Container) -> Dict:
        """Открыть контейнер и получить награду"""
        settings = container.CONTAINER_SETTINGS.get(container.container_type)
        if not settings:
            return {}

        # Генерация ресурсов
        resources = settings['resources']
        metal = random.randint(resources['min'], resources['max'])
        crystals = int(metal * 0.1 * random.uniform(0.5, 2.0))

        # Попытка выпадения предмета
        item = None
        roll = random.random()
        cumulative = 0
        for rarity, chance in settings['drop_chance'].items():
            cumulative += chance
            if roll <= cumulative:
                item = {'rarity': rarity, 'name': f'Предмет {rarity}'}
                break

        return {
            'metal': metal,
            'crystals': crystals,
            'item': item
        }

    @staticmethod
    def can_receive_container(current_count: int) -> bool:
        """Проверка, можно ли получить еще контейнер"""
        return current_count < ContainerSystem.MAX_CONTAINERS
