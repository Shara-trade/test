"""
3.4. Крит-система (x2, x5, x10)
"""
import random
from typing import Tuple, Optional
from enum import Enum


class CritType(Enum):
    NORMAL = 2  # x2
    RARE = 5  # x5
    EPIC = 10  # x10


class CritSystem:
    """Система критических ударов"""

    BASE_CRIT_CHANCE = 0.02

    CRIT_DISTRIBUTION = {
        CritType.NORMAL: 0.70,
        CritType.RARE: 0.20,
        CritType.EPIC: 0.10
    }

    @staticmethod
    def calculate_crit(base_chance: float = None) -> Tuple[bool, Optional[CritType]]:
        """Расчет крита. Returns: (is_crit, crit_type или None)"""
        chance = base_chance or CritSystem.BASE_CRIT_CHANCE

        if random.random() > chance:
            return False, None

        roll = random.random()
        cumulative = 0

        for crit_type, probability in CritSystem.CRIT_DISTRIBUTION.items():
            cumulative += probability
            if roll <= cumulative:
                return True, crit_type

        return True, CritType.NORMAL

    @staticmethod
    def get_crit_message(crit_type: CritType) -> str:
        """Получить сообщение для типа крита"""
        messages = {
            CritType.NORMAL: '💥 КРИТ x2!',
            CritType.RARE: '🔥 МЕГА-КРИТ x5!',
            CritType.EPIC: '⚡ УЛЬТРА-КРИТ x10!'
        }
        return messages.get(crit_type, '💥 КРИТ!')

    @staticmethod
    def apply_crit_multiplier(base_amount: int, crit_type: CritType) -> int:
        """Применить множитель крита к базовой сумме"""
        return int(base_amount * crit_type.value)
