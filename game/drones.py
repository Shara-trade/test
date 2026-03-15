"""
3.6. Система дронов (Idle-доход)
"""
import random
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Drone:
    """Модель дрона"""
    id: int
    user_id: int
    drone_type: str
    level: int = 1
    income_per_tick: int = 0
    module_slots: int = 1
    is_active: bool = True

    # Типы дронов
    DRONE_TYPES = {
        'basic': {
            'name': 'Базовый дрон',
            'base_income': 2,
            'slots': 1,
            'crit_chance': 0.01,
            'price_metal': 100
        },
        'miner': {
            'name': 'Шахтёр',
            'base_income': 8,
            'slots': 2,
            'crit_chance': 0.02,
            'price_metal': 500
        },
        'laser': {
            'name': 'Лазерный',
            'base_income': 25,
            'slots': 3,
            'crit_chance': 0.03,
            'price_metal': 2500
        },
        'quantum': {
            'name': 'Квантовый',
            'base_income': 70,
            'slots': 4,
            'crit_chance': 0.05,
            'price_metal': 10000,
            'price_crystals': 50
        },
        'ai': {
            'name': 'ИИ-дрон',
            'base_income': 200,
            'slots': 5,
            'crit_chance': 0.10,
            'price_metal': 50000,
            'price_crystals': 100,
            'price_dark_matter': 5
        }
    }

    @classmethod
    def get_drone_info(cls, drone_type: str) -> Optional[Dict]:
        """Получить информацию о типе дрона"""
        return cls.DRONE_TYPES.get(drone_type)

    @classmethod
    def calculate_income(cls, drone_type: str, level: int) -> int:
        """
        Расчет дохода дрона
        Каждый уровень +50% к базовому доходу
        """
        info = cls.get_drone_info(drone_type)
        if not info:
            return 0

        base_income = info['base_income']
        level_multiplier = 1 + ((level - 1) * 0.5)
        return int(base_income * level_multiplier)

    @classmethod
    def get_upgrade_cost(cls, drone_type: str, current_level: int) -> Dict[str, int]:
        """Стоимость улучшения дрона"""
        # Базовая формула: металл * уровень * 100, кристаллы * уровень * 10
        return {
            'metal': (current_level * 100) + 500,
            'crystals': (current_level * 10) + 10
        }


class DroneSystem:
    """Система управления дронами с синергией"""

    TICK_INTERVAL = 5  # Секунд между тиками
    MAX_DRONES = 50  # Максимум дронов на игрока
    MAX_DRONE_LEVEL = 10  # Максимальный уровень дрона

    @staticmethod
    def calculate_total_income(drones: List[Drone]) -> int:
        """
        Расчет общего пассивного дохода всех дронов.
        Базовый расчёт без синергии.
        """
        total = 0
        for drone in drones:
            if drone.is_active:
                total += Drone.calculate_income(drone.drone_type, drone.level)
        return total

    @staticmethod
    def calculate_income_with_synergy(drones: List[Drone]) -> Dict:
        """
        Расчет дохода с учётом синергии между дронами.
        
        Синергия даёт бонусы:
        - Бонус за количество дронов: +5% за каждого дрона
        - Бонус за разнообразие типов: +10% за каждый уникальный тип
        - Бонус за высокоуровневых дронов: +2% за каждый уровень выше 5
        
        Args:
            drones: Список дронов игрока
            
        Returns:
            Dict с ключами:
            - base_income: Базовый доход без бонусов
            - count_bonus: Бонус за количество (коэффициент)
            - variety_bonus: Бонус за разнообразие (коэффициент)
            - level_bonus: Бонус за уровень (коэффициент)
            - total_multiplier: Общий множитель
            - final_income: Итоговый доход
        """
        if not drones:
            return {
                'base_income': 0,
                'count_bonus': 1.0,
                'variety_bonus': 1.0,
                'level_bonus': 1.0,
                'total_multiplier': 1.0,
                'final_income': 0
            }
        
        # Фильтруем только активные дроны
        active_drones = [d for d in drones if d.is_active]
        
        if not active_drones:
            return {
                'base_income': 0,
                'count_bonus': 1.0,
                'variety_bonus': 1.0,
                'level_bonus': 1.0,
                'total_multiplier': 1.0,
                'final_income': 0
            }
        
        # Базовый доход
        base_income = sum(
            Drone.calculate_income(d.drone_type, d.level) 
            for d in active_drones
        )
        
        # Бонус за количество дронов: +5% за каждого
        count = len(active_drones)
        count_bonus = 1 + (count * 0.05)
        
        # Бонус за разнообразие типов: +10% за каждый уникальный тип
        unique_types = set(d.drone_type for d in active_drones)
        variety_bonus = 1 + (len(unique_types) * 0.10)
        
        # Бонус за высокоуровневых дронов: +2% за каждый уровень выше 5
        high_level_count = sum(1 for d in active_drones if d.level > 5)
        level_bonus = 1 + (high_level_count * 0.02)
        
        # Общий множитель
        total_multiplier = count_bonus * variety_bonus * level_bonus
        
        # Итоговый доход
        final_income = int(base_income * total_multiplier)
        
        return {
            'base_income': base_income,
            'count_bonus': round(count_bonus, 2),
            'variety_bonus': round(variety_bonus, 2),
            'level_bonus': round(level_bonus, 2),
            'total_multiplier': round(total_multiplier, 2),
            'final_income': final_income,
            'active_drones': count,
            'unique_types': len(unique_types),
            'high_level_count': high_level_count
        }

    @staticmethod
    def get_synergy_description(drones: List[Drone]) -> str:
        """
        Получить текстовое описание текущей синергии.
        
        Returns:
            Строка с описанием бонусов
        """
        result = DroneSystem.calculate_income_with_synergy(drones)
        
        if result['base_income'] == 0:
            return "Нет активных дронов"
        
        parts = []
        
        if result['count_bonus'] > 1.0:
            bonus_percent = int((result['count_bonus'] - 1) * 100)
            parts.append(f"📊 Количество: +{bonus_percent}%")
        
        if result['variety_bonus'] > 1.0:
            bonus_percent = int((result['variety_bonus'] - 1) * 100)
            parts.append(f"🎯 Разнообразие: +{bonus_percent}%")
        
        if result['level_bonus'] > 1.0:
            bonus_percent = int((result['level_bonus'] - 1) * 100)
            parts.append(f"⭐ Уровень: +{bonus_percent}%")
        
        if not parts:
            return "Базовый доход без бонусов"
        
        total_bonus = int((result['total_multiplier'] - 1) * 100)
        return f"{chr(10).join(parts)}{chr(10)}💫 Итого: +{total_bonus}%"

    @staticmethod
    def calculate_offline_income(
        drones: List[Drone],
        minutes_offline: int
    ) -> Dict[str, int]:
        """
        Расчет дохода за время оффлайн.
        Учитывает синергию дронов.
        Максимум 24 часа (1440 минут).
        """
        max_minutes = min(minutes_offline, 1440)
        ticks = max_minutes * 60 // DroneSystem.TICK_INTERVAL

        # Используем доход с синергией
        income_result = DroneSystem.calculate_income_with_synergy(drones)
        income_per_tick = income_result['final_income']
        total_income = income_per_tick * ticks

        # Распределение ресурсов
        metal = int(total_income * random.uniform(0.9, 1.1))
        crystals = int(metal * 0.1 * random.uniform(0.5, 1.5))

        return {
            'metal': metal,
            'crystals': crystals,
            'ticks': ticks,
            'synergy_multiplier': income_result['total_multiplier']
        }

    @staticmethod
    def can_buy_drone(current_drone_count: int) -> bool:
        """Проверка, можно ли купить еще дрона"""
        return current_drone_count < DroneSystem.MAX_DRONES

    @staticmethod
    def can_upgrade_drone(drone: Drone) -> bool:
        """Проверка, можно ли улучшить дрона"""
        return drone.level < DroneSystem.MAX_DRONE_LEVEL
