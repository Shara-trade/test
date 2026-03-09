"""
3.5. Редкий лут (система дропа)
"""
import random
from enum import Enum
from typing import Optional, Dict, List
from dataclasses import dataclass


class Rarity(Enum):
    COMMON = 'common'  # Обычный - 60%
    RARE = 'rare'  # Редкий - 25%
    EPIC = 'epic'  # Эпический - 12%
    LEGENDARY = 'legendary'  # Легендарный - 3%


@dataclass
class LootItem:
    """Предмет лута"""
    key: str
    name: str
    description: str
    rarity: Rarity
    emoji: str
    sell_price: int  # Базовая цена продажи
    item_type: str  # material, module, artifact


class LootSystem:
    """Система выпадения предметов при добыче"""

    BASE_DROP_CHANCE = 0.05  # 5% базовый шанс выпадения лута

    # Распределение редкости
    RARITY_DISTRIBUTION = {
        Rarity.COMMON: 0.60,
        Rarity.RARE: 0.25,
        Rarity.EPIC: 0.12,
        Rarity.LEGENDARY: 0.03,
    }

    # Предметы для выпадения при добыче
    LOOT_ITEMS = {
        Rarity.COMMON: [
            LootItem(
                key="scrap_metal",
                name="Металлолом",
                description="Обломки старых кораблей. Можно переработать.",
                rarity=Rarity.COMMON,
                emoji="🔩",
                sell_price=10,
                item_type="material"
            ),
            LootItem(
                key="wires",
                name="Провода",
                description="Медные провода из старых систем.",
                rarity=Rarity.COMMON,
                emoji="🔌",
                sell_price=15,
                item_type="material"
            ),
            LootItem(
                key="glass_shards",
                name="Осколки стекла",
                description="Остатки иллюминаторов.",
                rarity=Rarity.COMMON,
                emoji="🔷",
                sell_price=8,
                item_type="material"
            ),
        ],
        Rarity.RARE: [
            LootItem(
                key="drone_parts",
                name="Детали дрона",
                description="Функциональные части старых дронов.",
                rarity=Rarity.RARE,
                emoji="⚙️",
                sell_price=50,
                item_type="material"
            ),
            LootItem(
                key="energy_cell",
                name="Энергоячейка",
                description="Заряженная батарея. Восстанавливает 50 энергии.",
                rarity=Rarity.RARE,
                emoji="🔋",
                sell_price=100,
                item_type="consumable"
            ),
            LootItem(
                key="circuit_board",
                name="Платапо",
                description="Рабочая электронная плата.",
                rarity=Rarity.RARE,
                emoji="📟",
                sell_price=75,
                item_type="material"
            ),
        ],
        Rarity.EPIC: [
            LootItem(
                key="energy_crystal",
                name="Кристалл энергии",
                description="Кристалл с чистой энергией. Восстанавливает 200 энергии.",
                rarity=Rarity.EPIC,
                emoji="💠",
                sell_price=300,
                item_type="consumable"
            ),
            LootItem(
                key="nano_core",
                name="Нано-ядро",
                description="Микроскопический процессор древней цивилизации.",
                rarity=Rarity.EPIC,
                emoji="🧬",
                sell_price=500,
                item_type="artifact"
            ),
            LootItem(
                key="quantum_chip",
                name="Квантовый чип",
                description="Улучшает крит-шанс на 1% при установке.",
                rarity=Rarity.EPIC,
                emoji="💎",
                sell_price=400,
                item_type="module"
            ),
        ],
        Rarity.LEGENDARY: [
            LootItem(
                key="alien_alloy",
                name="Инопланетный сплав",
                description="Материал неизвестного происхождения. Очень ценный.",
                rarity=Rarity.LEGENDARY,
                emoji="🌟",
                sell_price=2000,
                item_type="artifact"
            ),
            LootItem(
                key="ai_fragment",
                name="Фрагмент ИИ",
                description="Часть древнего искусственного интеллекта.",
                rarity=Rarity.LEGENDARY,
                emoji="🤖",
                sell_price=3000,
                item_type="artifact"
            ),
        ],
    }

    @staticmethod
    def try_drop(luck_bonus: float = 0.0) -> Optional[LootItem]:
        """
        Попытка выпадения предмета при добыче.
        
        Args:
            luck_bonus: Бонус к шансу (0.0 = 0%, 0.5 = +50%)
        
        Returns:
            Предмет или None
        """
        total_chance = LootSystem.BASE_DROP_CHANCE + (LootSystem.BASE_DROP_CHANCE * luck_bonus)
        
        if random.random() > total_chance:
            return None

        # Определяем редкость
        rarity = LootSystem._roll_rarity()

        # Выбираем случайный предмет из категории
        items = LootSystem.LOOT_ITEMS.get(rarity, [])
        if not items:
            return None

        return random.choice(items)

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
        }
        return emojis.get(rarity, '⚪')

    @staticmethod
    def format_loot_message(item: LootItem) -> str:
        """Форматировать сообщение о найденном предмете"""
        emoji = LootSystem.get_rarity_emoji(item.rarity.value)
        return f"{emoji} Найден предмет: {item.emoji} {item.name}!"


# Глобальный экземпляр
loot_system = LootSystem()

