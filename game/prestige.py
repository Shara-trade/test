"""
3.9. Система престижа (Tech-очки)
"""
import math
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class PrestigeUpgrade:
    """Улучшение престижа"""
    id: str
    name: str
    description: str
    max_level: int
    base_cost: int  # В tech-очках
    effect_per_level: float

    PRESTIGE_UPGRADES = {
        'mining_efficiency': {
            'name': '⚙️ Эффективность добычи',
            'description': '+10% к добыче за клик за уровень',
            'max_level': 10,
            'base_cost': 1,
            'effect_per_level': 0.10
        },
        'drone_power': {
            'name': '🤖 Мощь дронов',
            'description': '+15% к пассивному доходу за уровень',
            'max_level': 10,
            'base_cost': 2,
            'effect_per_level': 0.15
        },
        'energy_capacity': {
            'name': '⚡ Ёмкость батарей',
            'description': '+20% к макс. энергии за уровень',
            'max_level': 5,
            'base_cost': 3,
            'effect_per_level': 0.20
        },
        'crit_chance': {
            'name': '💥 Шанс крита',
            'description': '+1% к шансу крита за уровень',
            'max_level': 5,
            'base_cost': 5,
            'effect_per_level': 0.01
        },
        'loot_quality': {
            'name': '⭐ Качество лута',
            'description': '+5% к шансу редких предметов за уровень',
            'max_level': 10,
            'base_cost': 2,
            'effect_per_level': 0.05
        },
        'exp_bonus': {
            'name': '📈 Опыт исследователя',
            'description': '+25% к получаемому опыту за уровень',
            'max_level': 5,
            'base_cost': 3,
            'effect_per_level': 0.25
        }
    }


class PrestigeSystem:
    """Система престижа"""

    PRESTIGE_REQUIREMENT = 1000000000  # 1 миллиард ресурсов
    BASE_TECH_TOKENS = 10  # Базовое количество tech-токенов

    @staticmethod
    def can_prestige(total_mined: int) -> bool:
        """Проверка, может ли игрок начать престиж"""
        return total_mined >= PrestigeSystem.PRESTIGE_REQUIREMENT

    @staticmethod
    def calculate_tech_tokens(total_mined: int, prestige_count: int) -> int:
        """
        Расчет tech-токенов за престиж
        Формула: база + бонус за избыток ресурсов + бонус за престиж
        """
        if not PrestigeSystem.can_prestige(total_mined):
            return 0

        base_tokens = PrestigeSystem.BASE_TECH_TOKENS

        # Бонус за избыток ресурсов
        overflow = total_mined - PrestigeSystem.PRESTIGE_REQUIREMENT
        overflow_bonus = int(math.log10(overflow / PrestigeSystem.PRESTIGE_REQUIREMENT + 1) * 5)

        # Бонус за количество престижей
        prestige_bonus = prestige_count * 2

        return base_tokens + overflow_bonus + prestige_bonus

    @staticmethod
    def get_prestige_cost(upgrade_id: str, current_level: int) -> int:
        """Расчет стоимости улучшения"""
        upgrade = PrestigeUpgrade.PRESTIGE_UPGRADES.get(upgrade_id)
        if not upgrade:
            return 0

        # Стоимость растет с уровнем
        return int(upgrade['base_cost'] * (1.5 ** current_level))

    @staticmethod
    def can_buy_upgrade(tech_tokens: int, upgrade_id: str, current_level: int) -> bool:
        """Проверка, можно ли купить улучшение"""
        upgrade = PrestigeUpgrade.PRESTIGE_UPGRADES.get(upgrade_id)
        if not upgrade:
            return False

        if current_level >= upgrade['max_level']:
            return False

        cost = PrestigeSystem.get_prestige_cost(upgrade_id, current_level)
        return tech_tokens >= cost

    @staticmethod
    def apply_prestige_reset() -> Dict:
        """
        Сброс прогресса при престиже
        Возвращает то, что нужно сбросить
        """
        return {
            'level': 1,
            'experience': 0,
            'metal': 0,
            'crystals': 0,
            'dark_matter': 0,
            'drones': [],  # Удалить всех дронов
            'inventory': [],  # Очистить инвентарь (кроме особых предметов)
            'current_system': 'alpha_7',
            'total_clicks': 0,
            # Сохраняется: tech_tokens, prestige_count, tech_upgrades
        }
