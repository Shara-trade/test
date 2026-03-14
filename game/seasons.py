"""
3.10. Система сезонов
Сезонные ивенты и награды
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum


class SeasonType(Enum):
    NORMAL = "normal"
    SPECIAL = "special"
    LEGENDARY = "legendary"


@dataclass
class SeasonReward:
    """Награда за уровень сезона"""
    level: int
    is_premium: bool
    metal: int = 0
    crystals: int = 0
    dark_matter: int = 0
    credits: int = 0
    quantum_tokens: int = 0
    item_key: Optional[str] = None
    item_quantity: int = 1


@dataclass
class Season:
    """Модель сезона"""
    season_id: int
    name: str
    theme: str
    season_type: SeasonType
    start_date: datetime
    end_date: datetime
    max_level: int = 100
    
    # Уникальные предметы сезона
    unique_items: List[str] = None
    
    @property
    def days_remaining(self) -> int:
        """Дней до конца сезона"""
        delta = self.end_date - datetime.now()
        return max(0, delta.days)
    
    @property
    def is_active(self) -> bool:
        """Активен ли сезон"""
        now = datetime.now()
        return self.start_date <= now <= self.end_date


class SeasonSystem:
    """Система сезонов"""
    
    SEASON_DURATION_DAYS = 30
    XP_PER_LEVEL_BASE = 1000
    
    # Действия и их награды в XP сезона
    XP_REWARDS = {
        "click": 1,
        "craft": 50,
        "sell": 20,
        "expedition_complete": 100,
        "boss_defeat": 200,
        "clan_raid": 150
    }
    
    @staticmethod
    def calculate_xp_for_level(level: int) -> int:
        """Рассчитать XP для достижения уровня"""
        return int(SeasonSystem.XP_PER_LEVEL_BASE * (1.2 ** (level - 1)))
    
    @staticmethod
    def get_action_xp(action: str) -> int:
        """Получить XP за действие"""
        return SeasonSystem.XP_REWARDS.get(action, 0)
    
    @staticmethod
    def calculate_level(total_xp: int) -> int:
        """Рассчитать текущий уровень по XP"""
        level = 1
        xp_needed = SeasonSystem.XP_PER_LEVEL_BASE
        
        while total_xp >= xp_needed:
            total_xp -= xp_needed
            level += 1
            xp_needed = int(xp_needed * 1.2)
        
        return level
    
    @staticmethod
    def get_season_progress(total_xp: int) -> Dict:
        """Получить прогресс сезона"""
        level = SeasonSystem.calculate_level(total_xp)
        xp_for_next = SeasonSystem.calculate_xp_for_level(level)
        
        # XP на текущем уровне
        xp_spent = 0
        for l in range(1, level):
            xp_spent += SeasonSystem.calculate_xp_for_level(l)
        
        xp_current = total_xp - xp_spent
        
        return {
            "level": level,
            "xp_current": xp_current,
            "xp_needed": xp_for_next,
            "progress_percent": int((xp_current / xp_for_next) * 100)
        }
    
    @staticmethod
    def generate_season_rewards(season_type: SeasonType, max_level: int = 100) -> List[SeasonReward]:
        """Генерация наград сезона"""
        rewards = []
        
        for level in range(1, max_level + 1):
            # Бесплатная награда (каждые 5 уровней)
            if level % 5 == 0:
                rewards.append(SeasonReward(
                    level=level,
                    is_premium=False,
                    metal=level * 100,
                    crystals=level * 10
                ))
            
            # Премиум награда (каждые 3 уровня)
            if level % 3 == 0:
                rewards.append(SeasonReward(
                    level=level,
                    is_premium=True,
                    metal=level * 200,
                    crystals=level * 20,
                    credits=level * 50
                ))
        
        # Особые награды на ключевых уровнях
        special_levels = [10, 25, 50, 75, 100]
        for lvl in special_levels:
            rewards.append(SeasonReward(
                level=lvl,
                is_premium=False,
                metal=lvl * 500,
                crystals=lvl * 50,
                dark_matter=lvl // 10
            ))
            rewards.append(SeasonReward(
                level=lvl,
                is_premium=True,
                metal=lvl * 1000,
                crystals=lvl * 100,
                quantum_tokens=lvl // 25
            ))
        
        return rewards


@dataclass
class UserSeasonProgress:
    """Прогресс пользователя в сезоне"""
    user_id: int
    season_id: int
    total_xp: int = 0
    premium_pass: bool = False
    claimed_rewards: List[int] = None
    
    def __post_init__(self):
        if self.claimed_rewards is None:
            self.claimed_rewards = []
    
    @property
    def level(self) -> int:
        return SeasonSystem.calculate_level(self.total_xp)
    
    def can_claim_reward(self, reward_level: int, is_premium: bool) -> bool:
        """Можно ли забрать награду"""
        if reward_level in self.claimed_rewards:
            return False
        if self.level < reward_level:
            return False
        if is_premium and not self.premium_pass:
            return False
        return True
