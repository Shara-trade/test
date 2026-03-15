"""
Система уровней и опыта
"""
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class LevelInfo:
    """Информация об уровне"""
    level: int
    exp_needed: int
    exp_total: int  # Суммарный опыт для достижения уровня
    energy_bonus: int
    mining_bonus: float
    title: str


class LevelSystem:
    """Система уровней"""
    
    # Бонусы за уровень
    ENERGY_PER_LEVEL = 50  # +50 макс. энергии за уровень
    MINING_BONUS_PER_LEVEL = 0.02  # +2% к добыче за уровень
    
    # Титулы по уровням
    TITLES = {
        range(1, 5): "Новичок",
        range(5, 10): "Шахтёр",
        range(10, 20): "Бурильщик",
        range(20, 30): "Сталкер",
        range(30, 40): "Космический волк",
        range(40, 50): "Звёздный капитан",
        range(50, 75): "Галактический барон",
        range(75, 100): "Император сектора",
        range(100, 999): "Легенда космоса",
    }
    
    @staticmethod
    def exp_for_level(level: int) -> int:
        """
        Опыт, необходимый для достижения уровня.
        
        Полиномиальная формула: 1000 * level * (1 + 0.1 * level)
        - Уровень 1: 1000 * 1 * 1.1 = 1100
        - Уровень 10: 1000 * 10 * 2.0 = 20000
        - Уровень 50: 1000 * 50 * 6.0 = 300000
        - Уровень 100: 1000 * 100 * 11.0 = 1100000
        """
        return int(1000 * level * (1 + level * 0.1))
    
    @staticmethod
    def total_exp_for_level(level: int) -> int:
        """Суммарный опыт для достижения уровня с 1"""
        total = 0
        for l in range(1, level):
            total += LevelSystem.exp_for_level(l)
        return total
    
    @staticmethod
    def get_level_from_exp(total_exp: int) -> int:
        """Получить уровень из общего опыта"""
        level = 1
        exp_spent = 0
        
        while True:
            exp_needed = LevelSystem.exp_for_level(level)
            if exp_spent + exp_needed > total_exp:
                return level
            exp_spent += exp_needed
            level += 1
    
    @staticmethod
    def get_level_info(level: int) -> LevelInfo:
        """Получить полную информацию об уровне"""
        level = level or 1  # Защита от None
        
        exp_needed = LevelSystem.exp_for_level(level)
        exp_total = LevelSystem.total_exp_for_level(level)
        energy_bonus = (level - 1) * LevelSystem.ENERGY_PER_LEVEL
        mining_bonus = (level - 1) * LevelSystem.MINING_BONUS_PER_LEVEL
        
        # Определяем титул
        title = "Неизвестный"
        for level_range, title_name in LevelSystem.TITLES.items():
            if level in level_range:
                title = title_name
                break
        
        return LevelInfo(
            level=level,
            exp_needed=exp_needed,
            exp_total=exp_total,
            energy_bonus=energy_bonus,
            mining_bonus=mining_bonus,
            title=title
        )
    
    @staticmethod
    def get_mining_bonus(level: int) -> float:
        """Получить бонус к добыче за уровень"""
        level = level or 1  # Защита от None
        return 1.0 + ((level - 1) * LevelSystem.MINING_BONUS_PER_LEVEL)
    
    @staticmethod
    def get_max_energy_bonus(level: int) -> int:
        """Получить бонус к макс. энергии за уровень"""
        level = level or 1  # Защита от None
        return (level - 1) * LevelSystem.ENERGY_PER_LEVEL
    
    @staticmethod
    def calculate_exp_reward(action: str, value: int = 1) -> int:
        """Рассчитать награду опыта за действие"""
        EXP_REWARDS = {
            "click": 1,           # За клик
            "craft": 10,          # За крафт
            "sell": 5,            # За продажу
            "expedition": 50,     # За экспедицию
            "boss_kill": 100,     # За убийство босса
            "container_open": 20, # За открытие контейнера
        }
        
        base_exp = EXP_REWARDS.get(action, 0)
        return base_exp * value
    
    @staticmethod
    def format_exp_bar(current_exp: int, exp_needed: int, width: int = 10) -> str:
        """Форматировать полоску опыта"""
        current_exp = current_exp or 0
        exp_needed = exp_needed or 1  # Избегаем деления на 0
        
        percent = min(100, (current_exp / exp_needed) * 100)
        filled = int(percent / (100 / width))
        empty = width - filled
        
        return "█" * filled + "░" * empty
    
    @staticmethod
    def get_progress_info(current_level: int, current_exp: int) -> Dict:
        """Получить информацию о прогрессе"""
        # Значения по умолчанию
        current_level = current_level or 1
        current_exp = current_exp or 0
        
        level_info = LevelSystem.get_level_info(current_level)
        next_level_info = LevelSystem.get_level_info(current_level + 1)
        
        exp_percent = int((current_exp / level_info.exp_needed) * 100) if level_info.exp_needed > 0 else 0
        exp_bar = LevelSystem.format_exp_bar(current_exp, level_info.exp_needed)
        
        return {
            "current_level": current_level,
            "current_exp": current_exp,
            "exp_needed": level_info.exp_needed,
            "exp_percent": exp_percent,
            "exp_bar": exp_bar,
            "title": level_info.title,
            "mining_bonus": level_info.mining_bonus,
            "energy_bonus": level_info.energy_bonus,
            "next_level": current_level + 1,
            "next_title": next_level_info.title,
        }
