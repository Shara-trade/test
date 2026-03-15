"""
3.1. Основной клик (Добыча астероида)

Модуль отвечает за расчёт добычи ресурсов при клике игрока.
Учитывает уровень, мощность дронов, бонусы модулей и перегрев.
"""
import random
from typing import Dict


class MiningSystem:
    """
    Система добычи ресурсов.
    
    Отвечает за расчёт количества ресурсов, получаемых игроком
    при клике по астероиду.
    
    Attributes:
        BASE_MINE_AMOUNT (int): Базовое количество металла за клик (10)
    
    Example:
        >>> result = MiningSystem.calculate_mining(
        ...     user_level=10,
        ...     drone_power=100,
        ...     modules_bonus=50
        ... )
        >>> print(result['metal'])
        25
    """

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
        Расчёт добычи за клик.
        
        Формула: base_mine = 10 + (drone_power * 0.5) + modules_bonus
        
        Args:
            user_level: Уровень игрока (влияет на бонусы)
            drone_power: Суммарная мощность дронов
            modules_bonus: Бонус от модулей в единицах
            system_multiplier: Глобальный множитель (события)
            heat_percent: Процент перегрева (0-100)
        
        Returns:
            Dict[str, int]: Словарь с ключами:
                - metal: количество металла
                - crystals: количество кристаллов
                - dark_matter: количество тёмной материи
        
        Example:
            >>> result = MiningSystem.calculate_mining(user_level=5)
            >>> result['metal'] > 0
            True
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
        """
        Стоимость клика в энергии.
        
        Returns:
            int: Количество энергии, расходуемое за клик (10)
        """
        return 10

    @staticmethod
    def can_click(current_energy: int) -> bool:
        """
        Проверка, достаточно ли энергии для клика.
        
        Args:
            current_energy: Текущее количество энергии
        
        Returns:
            bool: True если энергии достаточно для клика
        """
        return current_energy >= MiningSystem.get_click_cost()
