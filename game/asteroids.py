"""
Система астероидов
"""
import random
from dataclasses import dataclass
from typing import Dict, Tuple, Optional


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
    exp_bonus: float  # Множитель опыта
    color: str  # Цвет для отображения


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
            exp_bonus=1.0,
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
            exp_bonus=1.2,
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
            exp_bonus=1.5,
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
            exp_bonus=2.0,
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
            exp_bonus=3.0,
            color="🟠"
        ),
    ]
    
    @staticmethod
    def generate_asteroid() -> AsteroidType:
        """Сгенерировать случайный астероид"""
        roll = random.random()
        cumulative = 0
        
        for asteroid in AsteroidSystem.ASTEROID_TYPES:
            cumulative += asteroid.chance
            if roll< cumulative:
                return asteroid
        
        # Fallback к обычному
        return AsteroidSystem.ASTEROID_TYPES[0]
    
    @staticmethod
    def get_asteroid_rewards(asteroid: AsteroidType, mining_bonus: float = 1.0) -> Dict:
        """
        Рассчитать награду за добычу астероида.
        
        Args:
            asteroid: Тип астероида
            mining_bonus: Множитель добычи (от уровня, перегрева и т.д.)
        """
        metal = int(random.randint(asteroid.metal_min, asteroid.metal_max) * mining_bonus)
        crystals = int(random.randint(asteroid.crystals_min, asteroid.crystals_max) * mining_bonus)
        dark_matter = random.randint(asteroid.dark_matter_min, asteroid.dark_matter_max)
        
        # Тёмная материя не умножается на бонус
        dark_matter = min(dark_matter, asteroid.dark_matter_max)
        
        return {
            "asteroid": asteroid,
            "metal": metal,
            "crystals": crystals,
            "dark_matter": dark_matter,
            "exp_bonus": asteroid.exp_bonus
        }
    
    @staticmethod
    def format_mining_result(rewards: Dict, crit_multiplier: int = 1, is_crit: bool = False) -> str:
        """Форматировать результат добычи"""
        asteroid = rewards["asteroid"]
        metal = rewards["metal"] * crit_multiplier
        crystals = rewards["crystals"] * crit_multiplier
        dark_matter = rewards["dark_matter"] * crit_multiplier
        
        lines = [f"{asteroid.emoji} {asteroid.name} астероид!"]
        
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
    def get_asteroid_by_key(key: str) -> Optional[AsteroidType]:
        """Получить тип астероида по ключу"""
        for asteroid in AsteroidSystem.ASTEROID_TYPES:
            if asteroid.key == key:
                return asteroid
        return None


# Глобальный экземпляр
asteroid_system = AsteroidSystem()
