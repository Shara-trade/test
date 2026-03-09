"""
3.5. Редкий лут (система дропа)
"""
import random
from enum import Enum
from typing import Optional, Dict, List


class Rarity(Enum):
    COMMON = 'common'  # Обычный - 60%
    RARE = 'rare'  # Редкий - 25%
    EPIC = 'epic'  # Эпический - 10%
    LEGENDARY = 'legendary'  # Легендарный - 4%
    RELIC = 'relic'  # Реликт - 1%


class LootSystem:
    """Система выпадения предметов"""

    BASE_DROP_CHANCE = 0.03  # 3% базовый шанс

    # Распределение редкости
    RARITY_DISTRIBUTION = {
        Rarity.COMMON: 0.60,
        Rarity.RARE: 0.25,
        Rarity.EPIC: 0.10,
        Rarity.LEGENDARY: 0.04,
        Rarity.RELIC: 0.01
    }

    # Примеры предметов по редкости (заглушки)
    ITEMS = {
        Rarity.COMMON: [
            {'id': 'laser_mk1', 'name': 'Лазерный модуль Mk1', 'type': 'module'},
            {'id': 'battery_mk1', 'name': 'Батарея Mk1', 'type': 'module'},
            {'id': 'scanner_mk1', 'name': 'Сканер Mk1', 'type': 'module'}
        ],
        Rarity.RARE: [
            {'id': 'ancient_engine', 'name': 'Древний двигатель', 'type': 'artifact'},
            {'id': 'ai_core', 'name': 'Ядро ИИ', 'type': 'artifact'}
        ],
        Rarity.EPIC: [
            {'id': 'quantum_drill', 'name': 'Квантовый бур', 'type': 'module'},
            {'id': 'plasma_shield', 'name': 'Плазменный щит', 'type': 'module'}
        ],
        Rarity.LEGENDARY: [
            {'id': 'alien_artifact', 'name': 'Инопланетный артефакт', 'type': 'artifact'},
            {'id': 'neural_network', 'name': 'Нейросеть', 'type': 'module'}
        ],
        Rarity.RELIC: [
            {'id': 'galaxy_core', 'name': 'Ядро галактики', 'type': 'relic'},
            {'id': 'zero_element', 'name': 'Нулевой элемент', 'type': 'relic'}
        ]
    }

    @staticmethod
    def try_drop(luck_bonus: float = 0.0) -> Optional[Dict]:
        """
        Попытка выпадения предмета

        Args:
            luck_bonus: Бонус к шансу (0.0 = 0%)

        Returns:
            Предмет или None
        """
        total_chance = LootSystem.BASE_DROP_CHANCE + luck_bonus

        if random.random() > total_chance:
            return None

        # Определяем редкость
        rarity = LootSystem._roll_rarity()

        # Выбираем случайный предмет из категории
        items = LootSystem.ITEMS.get(rarity, [])
        if not items:
            return None

        item = random.choice(items).copy()
        item['rarity'] = rarity.value
        return item

    @staticmethod
    def _roll_rarity() -> Rarity:
        """Определение редкости выпавшего предмета"""
        roll = random.random()
        cumulative = 0

        for rarity, chance in LootSystem.RARITY_DISTRIBUTION.items():
            cumulative += chance
            if roll <= cumulative:
                return rarity

        return Rarity.COMMON

    @staticmethod
    def get_rarity_emoji(rarity: str) -> str:
        """Получить эмодзи для редкости"""
        emojis = {
            'common': '🔹',
            'rare': '🔸',
            'epic': '💜',
            'legendary': '💛',
            'relic': '⚜️'
        }
        return emojis.get(rarity, '⚪')
