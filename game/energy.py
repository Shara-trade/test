"""
3.2. Система энергии
"""
from typing import Dict
from datetime import datetime


class EnergySystem:
    """Система энергии игрока"""

    BASE_MAX_ENERGY = 1000
    ENERGY_REGEN_PER_MINUTE = 5
    BASE_CLICK_COST = 10

    @staticmethod
    def get_max_energy(user_level: int, battery_bonus: int = 0) -> int:
        """Расчет максимальной энергии: 1000 + (уровень * 50) + бонусы"""
        return EnergySystem.BASE_MAX_ENERGY + (user_level * 50) + battery_bonus

    @staticmethod
    def calculate_regeneration(last_activity: datetime) -> int:
        """Расчет восстановленной энергии за время оффлайн"""
        if not last_activity:
            return 0

        now = datetime.now()
        minutes_passed = int((now - last_activity).total_seconds() / 60)
        return min(minutes_passed * EnergySystem.ENERGY_REGEN_PER_MINUTE,
                   EnergySystem.BASE_MAX_ENERGY * 2)

    @staticmethod
    def get_energy_prices() -> Dict[int, Dict[str, int]]:
        """Цены на покупку энергии"""
        return {
            100: {'metal': 50, 'crystals': 0},
            500: {'metal': 200, 'crystals': 0},
            1000: {'metal': 350, 'crystals': 0}
        }

    @staticmethod
    def can_buy_energy(current_metal: int, current_crystals: int,
                       amount: int = 100) -> bool:
        """Проверка, может ли игрок купить энергию"""
        prices = EnergySystem.get_energy_prices()
        if amount not in prices:
            return False

        price = prices[amount]
        return (current_metal >= price['metal'] and
                current_crystals >= price['crystals'])
