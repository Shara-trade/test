"""
Система астероидов
"""
import random
from dataclasses import dataclass
from typing import Dict, Tuple, Optional
from enum import Enum


class AsteroidSize(Enum):
    """Размер астероида"""
    TINY = ("tiny", "Крошечный", "🔹", 0.5, 1)
    SMALL = ("small", "Маленький", "🔸", 1.0, 2)
    MEDIUM = ("medium", "Средний", "🔶", 1.5, 3)
    LARGE = ("large", "Крупный", "🔴", 2.0, 4)
    MASSIVE = ("massive", "Огромный", "🟣", 3.0, 5)
    
    def __init__(self, key: str, name: str, emoji: str, exp_mult: float, resource_mult: float):
        self._key = key
        self._name = name
        self._emoji = emoji
        self._exp_mult = exp_mult
        self._resource_mult = resource_mult
    
    @property
    def key(self) -> str:
        return self._key
    
    @property
    def display_name(self) -> str:
        return self._name
    
    @property
    def emoji(self) -> str:
        return self._emoji
    
    @property
    def exp_multiplier(self) -> float:
        return self._exp_mult
    
    @property
    def resource_multiplier(self) -> float:
        return self._resource_mult


@dataclass
class AsteroidType:
    """Тип астероида"""
    key: str
    name: str
    emoji: str
    chance: float  # Шанс выпадения (0-1)
    metal_min: int
    metal_max: int
    crystals_min: int
    crystals_max: int
    dark_matter_min: int
    dark_matter_max: int
    exp_reward: int  # Базовый опыт за этот тип
    color: str  # Цвет для отображения


@dataclass
class Asteroid:
    """Конкретный астероид (тип + размер)"""
    asteroid_type: AsteroidType
    size: AsteroidSize
    
    @property
    def key(self) -> str:
        return self.asteroid_type.key
    
    @property
    def name(self) -> str:
        return f"{self.size.display_name} {self.asteroid_type.name}"
    
    @property
    def emoji(self) -> str:
        return self.asteroid_type.emoji
    
    @property
    def exp_reward(self) -> int:
        """Базовый опыт с учётом размера"""
        import math
        return max(1, math.ceil(self.asteroid_type.exp_reward * self.size.exp_multiplier))
    
    @property
    def resource_multiplier(self) -> float:
        """Множитель ресурсов от размера"""
        return self.size.resource_multiplier


class AsteroidSystem:
    """Система генерации астероидов"""
    
    # Типы астероидов (сортированы по шансу)
    ASTEROID_TYPES = [
        AsteroidType(
            key="common",
            name="Обычный",
            emoji="🪨",
            chance=0.60,
            metal_min=8, metal_max=12,
            crystals_min=0, crystals_max=1,
            dark_matter_min=0, dark_matter_max=0,
            exp_reward=1,
            color="⚪"
        ),
        AsteroidType(
            key="iron",
            name="Железный",
            emoji="🪙",
            chance=0.25,
            metal_min=15, metal_max=25,
            crystals_min=1, crystals_max=3,
            dark_matter_min=0, dark_matter_max=0,
            exp_reward=2,
            color="🟡"
        ),
        AsteroidType(
            key="crystal",
            name="Кристаллический",
            emoji="💎",
            chance=0.10,
            metal_min=5, metal_max=10,
            crystals_min=5, crystals_max=15,
            dark_matter_min=0, dark_matter_max=1,
            exp_reward=5,
            color="🔵"
        ),
        AsteroidType(
            key="rare",
            name="Редкий",
            emoji="⚫",
            chance=0.04,
            metal_min=20, metal_max=40,
            crystals_min=10, crystals_max=20,
            dark_matter_min=1, dark_matter_max=3,
            exp_reward=10,
            color="🟣"
        ),
        AsteroidType(
            key="legendary",
            name="Легендарный",
            emoji="🌟",
            chance=0.01,
            metal_min=50, metal_max=100,
            crystals_min=30, crystals_max=50,
            dark_matter_min=5, dark_matter_max=10,
            exp_reward=20,
            color="🟠"
        ),
    ]
    
    # Шансы размеров
    SIZE_CHANCES = {
        AsteroidSize.TINY: 0.30,
        AsteroidSize.SMALL: 0.35,
        AsteroidSize.MEDIUM: 0.20,
        AsteroidSize.LARGE: 0.12,
        AsteroidSize.MASSIVE: 0.03,
    }
    
    @staticmethod
    def generate_asteroid() -> Asteroid:
        """Сгенерировать случайный астероид с типом и размером"""
        # Выбираем тип
        asteroid_type = AsteroidSystem._select_type()
        
        # Выбираем размер
        size = AsteroidSystem._select_size()
        
        return Asteroid(asteroid_type=asteroid_type, size=size)
    
    @staticmethod
    def _select_type() -> AsteroidType:
        """Выбрать тип астероида"""
        roll = random.random()
        cumulative = 0
        
        for asteroid in AsteroidSystem.ASTEROID_TYPES:
            cumulative += asteroid.chance
            if roll < cumulative:
                return asteroid
        
        # Fallback к обычному
        return AsteroidSystem.ASTEROID_TYPES[0]
    
    @staticmethod
    def _select_size() -> AsteroidSize:
        """Выбрать размер астероида"""
        roll = random.random()
        cumulative = 0
        
        for size, chance in AsteroidSystem.SIZE_CHANCES.items():
            cumulative += chance
            if roll < cumulative:
                return size
        
        return AsteroidSize.SMALL
    
    @staticmethod
    def get_asteroid_rewards(asteroid: Asteroid, mining_bonus: float = 1.0) -> Dict:
        """
        Рассчитать награду за добычу астероида.
        
        Args:
            asteroid: Астероид (тип + размер)
            mining_bonus: Множитель добычи (от уровня, перегрева и т.д.)
        """
        asteroid_type = asteroid.asteroid_type
        size_mult = asteroid.resource_multiplier
        
        metal = int(random.randint(asteroid_type.metal_min, asteroid_type.metal_max) * mining_bonus * size_mult)
        crystals = int(random.randint(asteroid_type.crystals_min, asteroid_type.crystals_max) * mining_bonus * size_mult)
        dark_matter = random.randint(asteroid_type.dark_matter_min, asteroid_type.dark_matter_max)
        
        # Тёмная материя не умножается на бонус размера
        dark_matter = min(dark_matter, asteroid_type.dark_matter_max)
        
        return {
            "asteroid": asteroid,
            "metal": metal,
            "crystals": crystals,
            "dark_matter": dark_matter,
            "exp_reward": asteroid.exp_reward,
        }
    
    @staticmethod
    def format_mining_result(rewards: Dict, crit_multiplier: int = 1, is_crit: bool = False) -> str:
        """Форматировать результат добычи"""
        asteroid = rewards["asteroid"]
        metal = rewards["metal"] * crit_multiplier
        crystals = rewards["crystals"] * crit_multiplier
        dark_matter = rewards["dark_matter"] * crit_multiplier
        
        lines = [f"{asteroid.emoji} {asteroid.name}!"]
        
        if is_crit:
            lines[0] = f"💥 КРИТ! {asteroid.emoji} {asteroid.name}!"
        
        reward_parts = []
        if metal > 0:
            reward_parts.append(f"+{metal} металла")
        if crystals > 0:
            reward_parts.append(f"+{crystals} кристаллов")
        if dark_matter > 0:
            reward_parts.append(f"+{dark_matter} тёмной материи")
        
        if reward_parts:
            lines.append(" | ".join(reward_parts))
        
        return "\n".join(lines)
    
    @staticmethod
    def get_asteroid_type_by_key(key: str) -> Optional[AsteroidType]:
        """Получить тип астероида по ключу"""
        for asteroid in AsteroidSystem.ASTEROID_TYPES:
            if asteroid.key == key:
                return asteroid
        return None


# Глобальный экземпляр
asteroid_system = AsteroidSystem()
