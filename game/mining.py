"""
3.1. Основной клик (Добыча астероида)
"""
import random
from typing import Dict


class MiningSystem:
    """Система добычи ресурсов"""

    BASE_MINE_AMOUNT = 10

    @staticmethod
    def calculate_mining(
        user_level: int,
        drone_power: int = 0,
        modules_bonus: int = 0,
        system_multiplier: float = 1.0,
        heat_percent: float = 0.0
    ) -> Dict[str, int]:
        """
        Расчет добычи за клик
        Формула: base_mine = 10 + (drone_power * 0.5) + modules_bonus
        """
        base_mine = MiningSystem.BASE_MINE_AMOUNT + (drone_power * 0.5) + modules_bonus
        heat_bonus = min(heat_percent / 100 * 0.5, 0.5) if heat_percent <= 80 else 0

        metal_gain = int(base_mine * system_multiplier * (1 + heat_bonus) * random.uniform(0.8, 1.2))
        crystal_gain = int(metal_gain * 0.1 * random.uniform(0.5, 1.5))
        dark_matter_gain = 1 if random.random() < 0.01 else 0

        return {
            'metal': metal_gain,
            'crystals': crystal_gain,
            'dark_matter': dark_matter_gain
        }

    @staticmethod
    def get_click_cost() -> int:
        """Стоимость клика в энергии"""
        return 10

    @staticmethod
    def can_click(current_energy: int) -> bool:
        """Проверка, достаточно ли энергии для клика"""
        return current_energy >= MiningSystem.get_click_cost()
