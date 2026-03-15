"""
3.12. Система экспедиций
"""
import random
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class ExpeditionType(Enum):
    NEAR_SPACE = 'near_space'  # 30 мин, 1 дрон
    ASTEROID_BELT = 'asteroid_belt'  # 2 часа, 3 дрона
    NEBULA = 'nebula'  # 8 часов, 5 дронов


@dataclass
class Expedition:
    """Модель экспедиции"""
    id: int
    user_id: int
    expedition_type: ExpeditionType
    drones_sent: int
    status: str  # 'active', 'completed', 'cancelled'
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    EXPEDITION_SETTINGS = {
        ExpeditionType.NEAR_SPACE: {
            'duration_minutes': 30,
            'drones_required': 1,
            'rewards': {
                'resources_chance': 0.80,
                'item_chance': 0.20,
                'artifact_chance': 0.00
            },
            'resources': {'min': 100, 'max': 500}
        },
        ExpeditionType.ASTEROID_BELT: {
            'duration_minutes': 120,
            'drones_required': 3,
            'rewards': {
                'resources_chance': 0.50,
                'item_chance': 0.40,
                'artifact_chance': 0.10
            },
            'resources': {'min': 500, 'max': 2000}
        },
        ExpeditionType.NEBULA: {
            'duration_minutes': 480,
            'drones_required': 5,
            'rewards': {
                'resources_chance': 0.30,
                'item_chance': 0.50,
                'artifact_chance': 0.20
            },
            'resources': {'min': 2000, 'max': 10000}
        }
    }

    def get_end_time(self) -> Optional[datetime]:
        """Получить время окончания"""
        if self.start_time:
            settings = self.EXPEDITION_SETTINGS.get(self.expedition_type)
            if settings:
                return self.start_time + timedelta(minutes=settings['duration_minutes'])
        return None

    def is_completed(self) -> bool:
        """Проверка, завершена ли экспедиция"""
        if self.status != 'active':
            return self.status == 'completed'

        end_time = self.get_end_time()
        if end_time:
            return datetime.now() >= end_time
        return False

    def get_time_remaining(self) -> Optional[timedelta]:
        """Получить оставшееся время"""
        if self.status != 'active':
            return None

        end_time = self.get_end_time()
        if end_time:
            remaining = end_time - datetime.now()
            return remaining if remaining.total_seconds() > 0 else timedelta(0)
        return None


class ExpeditionSystem:
    """Система экспедиций"""

    MAX_ACTIVE_EXPEDITIONS = 3  # Максимум активных экспедиций на игрока

    @staticmethod
    def can_start_expedition(
        user_drones: int,
        expedition_type: ExpeditionType,
        active_expeditions: int
    ) -> tuple[bool, str]:
        """
        Проверка, можно ли начать экспедицию

        Returns:
            (можно_ли, сообщение)
        """
        if active_expeditions >= ExpeditionSystem.MAX_ACTIVE_EXPEDITIONS:
            return False, 'Достигнут лимит активных экспедиций (3)'

        settings = expedition_type.EXPEDITION_SETTINGS.get(expedition_type)
        if not settings:
            return False, 'Неизвестный тип экспедиции'

        required_drones = settings['drones_required']
        if user_drones < required_drones:
            return False, f'Нужно {required_drones} дронов (у тебя {user_drones})'

        return True, 'OK'

    @staticmethod
    def calculate_rewards(expedition: Expedition) -> Dict:
        """Расчет наград за экспедицию"""
        settings = expedition.EXPEDITION_SETTINGS.get(expedition.expedition_type)
        if not settings:
            return {}

        rewards = settings['rewards']
        result = {'metal': 0, 'crystals': 0, 'items': [], 'artifacts': []}

        # Ресурсы
        if random.random() < rewards['resources_chance']:
            resources = settings['resources']
            result['metal'] = random.randint(resources['min'], resources['max'])
            result['crystals'] = int(result['metal'] * 0.1 * random.uniform(0.5, 2.0))

        # Предметы
        if random.random() < rewards['item_chance']:
            result['items'].append({'name': 'Случайный предмет', 'rarity': 'random'})

        # Артефакты
        if random.random() < rewards['artifact_chance']:
            result['artifacts'].append({'name': 'Древний артефакт', 'rarity': 'epic'})

        return result

    @staticmethod
    def get_expedition_info(expedition_type: ExpeditionType) -> Dict:
        """Получить информацию об экспедиции"""
        settings = expedition_type.EXPEDITION_SETTINGS.get(expedition_type)
        if not settings:
            return {}

        return {
            'name': {
                ExpeditionType.NEAR_SPACE: '🚀 Ближний космос',
                ExpeditionType.ASTEROID_BELT: '🚀 Пояс астероидов',
                ExpeditionType.NEBULA: '🚀 Туманность'
            }.get(expedition_type, 'Неизвестно'),
            'duration': settings['duration_minutes'],
            'drones_required': settings['drones_required'],
            'description': {
                ExpeditionType.NEAR_SPACE: 'Шансы: 80% ресурсы, 20% предметы',
                ExpeditionType.ASTEROID_BELT: 'Шансы: 50% ресурсы, 40% предметы, 10% артефакты',
                ExpeditionType.NEBULA: 'Шансы: 30% ресурсы, 50% предметы, 20% легендарные'
            }.get(expedition_type, '')
        }
