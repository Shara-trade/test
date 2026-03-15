"""
Система лута при добыче
Выпадение материалов из новой системы (materials.py)
"""
import random
from typing import Optional
from dataclasses import dataclass

from game.materials import MaterialSystem, MaterialGroup


@dataclass
class LootItem:
    """Предмет лута"""
    key: str
    name: str
    emoji: str
    group: MaterialGroup
    base_price: int


class LootSystem:
    """Система выпадения материалов при добыче"""

    BASE_DROP_CHANCE = 0.05  # 5% базовый шанс выпадения материала

    # Распределение по группам
    GROUP_DISTRIBUTION = {
        MaterialGroup.COMMON: 0.60,   # 60% - обычные материалы
        MaterialGroup.RARE: 0.30,     # 30% - редкие материалы
        MaterialGroup.EPIC: 0.10,     # 10% - эпические материалы
    }

    @staticmethod
    def try_drop(luck_bonus: float = 0.0) -> Optional[LootItem]:
        """
        Попытка выпадения материала при добыче.
        
        Args:
            luck_bonus: Бонус к шансу (0.0 = 0%, 0.5 = +50%)
        
        Returns:
            LootItem или None
        """
        total_chance = LootSystem.BASE_DROP_CHANCE + (LootSystem.BASE_DROP_CHANCE * luck_bonus)
        
        if random.random() > total_chance:
            return None

        # Определяем группу
        group = LootSystem._roll_group()

        # Выбираем случайный материал из группы
        materials = MaterialSystem.get_materials_by_group(group)
        if not materials:
            return None

        material = random.choice(materials)
        
        return LootItem(
            key=material.key,
            name=material.name,
            emoji=material.emoji,
            group=material.group,
            base_price=material.base_price
        )

    @staticmethod
    def _roll_group() -> MaterialGroup:
        """Определение группы выпавшего материала"""
        roll = random.random()
        cumulative = 0

        for group, chance in LootSystem.GROUP_DISTRIBUTION.items():
            cumulative += chance
            if roll <= cumulative:
                return group

        return MaterialGroup.COMMON

    @staticmethod
    def get_rarity_emoji(group: MaterialGroup) -> str:
        """Получить эмодзи для группы"""
        emojis = {
            MaterialGroup.COMMON: '🔹',
            MaterialGroup.RARE: '🔸',
            MaterialGroup.EPIC: '💜',
        }
        return emojis.get(group, '⚪')

    @staticmethod
    def format_loot_message(item: LootItem) -> str:
        """Форматировать сообщение о найденном материале"""
        emoji = LootSystem.get_rarity_emoji(item.group)
        return f"{emoji} Найден материал: {item.emoji} {item.name}!"


# Глобальный экземпляр
loot_system = LootSystem()

