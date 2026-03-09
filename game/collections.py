"""
3.8. Система коллекций (сеты предметов)
"""
from typing import Dict, List, Set
from dataclasses import dataclass


@dataclass
class Collection:
    """Модель коллекции"""
    id: str
    name: str
    description: str
    items_required: List[str]  # ID предметов
    reward_bonus: Dict  # Бонус за сборку

    COLLECTIONS = {
        'ancient_artifacts': {
            'name': '🏛 Древние артефакты',
            'description': 'Собери все древние реликвии',
            'items': [
                'ancient_engine',
                'alien_crystal',
                'portal_ruins',
                'forgotten_scroll',
                'primordial_core'
            ],
            'reward': {
                'type': 'mining_bonus',
                'value': 0.20  # +20% к добыче
            }
        },
        'drone_mastery': {
            'name': '🤖 Мастер дронов',
            'description': 'Все типы дронов в коллекции',
            'items': [
                'basic_drone_blueprint',
                'miner_drone_blueprint',
                'laser_drone_blueprint',
                'quantum_drone_blueprint',
                'ai_drone_blueprint'
            ],
            'reward': {
                'type': 'drone_bonus',
                'value': 0.25  # +25% к доходу дронов
            }
        },
        'laser_technology': {
            'name': '🔦 Лазерные технологии',
            'description': 'Все лазерные модули от Mk1 до Mk5',
            'items': [
                'laser_mk1',
                'laser_mk2',
                'laser_mk3',
                'laser_mk4',
                'laser_mk5'
            ],
            'reward': {
                'type': 'crit_bonus',
                'value': 0.05  # +5% к криту
            }
        },
        'cosmic_explorer': {
            'name': '🌌 Космический исследователь',
            'description': 'Посети все системы галактики',
            'items': [
                'alpha_7_token',
                'kepler_belt_token',
                'nebula_omega_token',
                'void_sector_token',
                'quantum_rift_token'
            ],
            'reward': {
                'type': 'loot_bonus',
                'value': 0.10  # +10% к шансу лута
            }
        }
    }


class CollectionSystem:
    """Система коллекций"""

    @staticmethod
    def get_collection_progress(collection_id: str, user_items: Set[str]) -> Dict:
        """
        Получить прогресс коллекции

        Args:
            collection_id: ID коллекции
            user_items: Множество ID предметов пользователя

        Returns:
            Словарь с прогрессом
        """
        collection = Collection.COLLECTIONS.get(collection_id)
        if not collection:
            return {'found': 0, 'total': 0, 'percent': 0}

        items = collection['items']
        found = sum(1 for item in items if item in user_items)
        total = len(items)
        percent = int((found / total) * 100) if total > 0 else 0

        return {
            'found': found,
            'total': total,
            'percent': percent,
            'missing': [item for item in items if item not in user_items],
            'completed': found == total
        }

    @staticmethod
    def check_collection_complete(collection_id: str, user_items: Set[str]) -> bool:
        """Проверка, собрана ли коллекция"""
        progress = CollectionSystem.get_collection_progress(collection_id, user_items)
        return progress['completed']

    @staticmethod
    def get_collection_reward(collection_id: str) -> Dict:
        """Получить награду за коллекцию"""
        collection = Collection.COLLECTIONS.get(collection_id)
        if not collection:
            return {}
        return collection['reward']

    @staticmethod
    def get_all_collections_progress(user_items: Set[str]) -> Dict[str, Dict]:
        """Получить прогресс всех коллекций"""
        result = {}
        for collection_id in Collection.COLLECTIONS:
            result[collection_id] = CollectionSystem.get_collection_progress(
                collection_id, user_items
            )
        return result
