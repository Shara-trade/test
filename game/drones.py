"""
Система дронов (Idle-доход)
Техническое задание: dron.txt
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta


# Эмодзи уровней дронов
LEVEL_EMOJI = {
    1: "⚪️",
    2: "🟢",
    3: "🟣",
    4: "🔴",
    5: "🟡"
}

# Слоты модулей по уровням
MODULE_SLOTS = {
    1: 0,
    2: 1,
    3: 2,
    4: 3,
    5: 4
}

# Конфигурация дронов по ТЗ
DRONE_CONFIG = {
    'basic': {
        'name': 'Базовый дрон',
        'emoji': '🤖',
        'resource': 'metal',  # Добываемый ресурс
        'price': {'metal': 7500, 'crystals': 0, 'dark_matter': 0},
        'income': {
            1: {'metal': 30, 'crystals': 0, 'dark_matter': 0},
            2: {'metal': 95, 'crystals': 0, 'dark_matter': 0},
            3: {'metal': 230, 'crystals': 0, 'dark_matter': 0},
            4: {'metal': 620, 'crystals': 0, 'dark_matter': 0},
            5: {'metal': 1860, 'crystals': 0, 'dark_matter': 0}
        }
    },
    'miner': {
        'name': 'Шахтёр',
        'emoji': '⛏️',
        'resource': 'mixed',  # Металл + Кристаллы
        'price': {'metal': 10000, 'crystals': 7500, 'dark_matter': 0},
        'income': {
            1: {'metal': 40, 'crystals': 30, 'dark_matter': 0},
            2: {'metal': 120, 'crystals': 95, 'dark_matter': 0},
            3: {'metal': 300, 'crystals': 230, 'dark_matter': 0},
            4: {'metal': 800, 'crystals': 620, 'dark_matter': 0},
            5: {'metal': 2400, 'crystals': 1860, 'dark_matter': 0}
        }
    },
    'laser': {
        'name': 'Лазерный',
        'emoji': '⚡',
        'resource': 'crystals',
        'price': {'metal': 0, 'crystals': 15000, 'dark_matter': 0},
        'income': {
            1: {'metal': 0, 'crystals': 60, 'dark_matter': 0},
            2: {'metal': 0, 'crystals': 180, 'dark_matter': 0},
            3: {'metal': 0, 'crystals': 450, 'dark_matter': 0},
            4: {'metal': 0, 'crystals': 1200, 'dark_matter': 0},
            5: {'metal': 0, 'crystals': 3600, 'dark_matter': 0}
        }
    },
    'quantum': {
        'name': 'Квантовый',
        'emoji': '🌀',
        'resource': 'dark_matter',
        'price': {'metal': 0, 'crystals': 0, 'dark_matter': 20000},
        'income': {
            1: {'metal': 0, 'crystals': 0, 'dark_matter': 80},
            2: {'metal': 0, 'crystals': 0, 'dark_matter': 240},
            3: {'metal': 0, 'crystals': 0, 'dark_matter': 600},
            4: {'metal': 0, 'crystals': 0, 'dark_matter': 1600},
            5: {'metal': 0, 'crystals': 0, 'dark_matter': 4800}
        }
    },
    'ai': {
        'name': 'ИИ-дрон',
        'emoji': '🧠',
        'resource': 'all',  # Все ресурсы
        'price': {'metal': 20000, 'crystals': 20000, 'dark_matter': 20000},
        'income': {
            1: {'metal': 80, 'crystals': 80, 'dark_matter': 80},
            2: {'metal': 240, 'crystals': 240, 'dark_matter': 240},
            3: {'metal': 600, 'crystals': 600, 'dark_matter': 600},
            4: {'metal': 1600, 'crystals': 1600, 'dark_matter': 1600},
            5: {'metal': 4800, 'crystals': 4800, 'dark_matter': 4800}
        }
    }
}

# Типы дронов в порядке отображения
DRONE_TYPES = ['basic', 'miner', 'laser', 'quantum', 'ai']

# Максимальный уровень дрона
MAX_DRONE_LEVEL = 5

# Лимит дронов в найме
MAX_HIRED_DRONES = 50

# Длительность миссии в минутах
MISSION_DURATION_MINUTES = 120

# Время до сгорания ресурсов (24 часа в минутах)
STORAGE_EXPIRE_MINUTES = 1440


class DroneSystem:
    """Система управления дронами по ТЗ"""
    
    @staticmethod
    def get_level_emoji(level: int) -> str:
        """Получить эмодзи уровня"""
        return LEVEL_EMOJI.get(level, "⚪️")
    
    @staticmethod
    def get_module_slots(level: int) -> int:
        """Получить количество слотов модулей"""
        return MODULE_SLOTS.get(level, 0)
    
    @staticmethod
    def get_drone_config(drone_type: str) -> Optional[Dict]:
        """Получить конфигурацию типа дрона"""
        return DRONE_CONFIG.get(drone_type)
    
    @staticmethod
    def get_income(drone_type: str, level: int) -> Dict[str, int]:
        """
        Получить доход дрона в минуту
        
        Returns:
            Dict с ключами: metal, crystals, dark_matter
        """
        config = DRONE_CONFIG.get(drone_type)
        if not config:
            return {'metal': 0, 'crystals': 0, 'dark_matter': 0}
        
        return config['income'].get(level, {'metal': 0, 'crystals': 0, 'dark_matter': 0})
    
    @staticmethod
    def get_price(drone_type: str) -> Dict[str, int]:
        """Получить цену покупки дрона 1 уровня"""
        config = DRONE_CONFIG.get(drone_type)
        if not config:
            return {'metal': 0, 'crystals': 0, 'dark_matter': 0}
        
        return config['price']
    
    @staticmethod
    def get_sell_price(drone_type: str, level: int) -> Dict[str, int]:
        """
        Рассчитать цену продажи дрона (30% от стоимости создания)
        
        Для дронов выше 1 уровня:
        Стоимость = количество дронов 1 уровня × цена 1 уровня
        """
        config = DRONE_CONFIG.get(drone_type)
        if not config:
            return {'metal': 0, 'crystals': 0, 'dark_matter': 0}
        
        base_price = config['price']
        
        # Количество дронов 1 уровня, потраченных на создание
        drones_needed = 5 ** (level - 1)
        
        sell_price = {
            'metal': int(base_price['metal'] * drones_needed * 0.3),
            'crystals': int(base_price['crystals'] * drones_needed * 0.3),
            'dark_matter': int(base_price['dark_matter'] * drones_needed * 0.3)
        }
        
        return sell_price
    
    @staticmethod
    def calculate_total_drones(drones_data: Dict) -> int:
        """
        Подсчитать общее количество дронов
        
        Args:
            drones_data: Dict с полями base_lvl1, base_lvl2, ... ai_lvl5
            
        Returns:
            Общее количество дронов
        """
        total = 0
        for drone_type in DRONE_TYPES:
            for level in range(1, 6):
                key = f"{drone_type}_lvl{level}"
                total += drones_data.get(key, 0)
        return total
    
    @staticmethod
    def calculate_income_per_minute(drones_data: Dict, hired_count: int = 0) -> Dict[str, int]:
        """
        Рассчитать общий доход в минуту от всех дронов
        
        Args:
            drones_data: Dict с количеством дронов по типам и уровням
            hired_count: Количество дронов в найме (если 0, доход = 0)
            
        Returns:
            Dict с доходом: metal, crystals, dark_matter
        """
        if hired_count == 0:
            return {'metal': 0, 'crystals': 0, 'dark_matter': 0}
        
        total_income = {'metal': 0, 'crystals': 0, 'dark_matter': 0}
        
        # Считаем доход от каждого типа и уровня
        for drone_type in DRONE_TYPES:
            for level in range(1, 6):
                key = f"{drone_type}_lvl{level}"
                count = drones_data.get(key, 0)
                
                if count > 0:
                    income = DroneSystem.get_income(drone_type, level)
                    total_income['metal'] += income['metal'] * count
                    total_income['crystals'] += income['crystals'] * count
                    total_income['dark_matter'] += income['dark_matter'] * count
        
        return total_income
    
    @staticmethod
    def can_upgrade(drones_data: Dict, drone_type: str, current_level: int, count: int = 1) -> Tuple[bool, str]:
        """
        Проверить, можно ли улучшить дронов
        
        Args:
            drones_data: Dict с количеством дронов
            drone_type: Тип дрона
            current_level: Текущий уровень (1-4)
            count: Количество улучшений
            
        Returns:
            (bool, error_message)
        """
        if current_level >= MAX_DRONE_LEVEL:
            return False, "Достигнут максимальный уровень"
        
        key = f"{drone_type}_lvl{current_level}"
        available = drones_data.get(key, 0)
        needed = 5 * count
        
        if available < needed:
            return False, f"Недостаточно свободных дронов для улучшения. Доступно: {available}"
        
        return True, ""
    
    @staticmethod
    def calculate_max_upgrades(available_drones: int) -> int:
        """
        Рассчитать максимальное количество улучшений
        
        Args:
            available_drones: Количество доступных дронов текущего уровня
            
        Returns:
            Максимальное количество улучшений
        """
        return available_drones // 5
    
    @staticmethod
    def can_hire(drones_data: Dict, drones_hired: int, drone_type: str, level: int, count: int = 1) -> Tuple[bool, str]:
        """
        Проверить, можно ли нанять дронов
        
        Args:
            drones_data: Dict с количеством дронов
            drones_hired: Текущее количество в найме
            drone_type: Тип дрона
            level: Уровень дрона
            count: Количество для найма
            
        Returns:
            (bool, error_message)
        """
        # Проверка лимита найма
        free_slots = MAX_HIRED_DRONES - drones_hired
        if free_slots <= 0:
            return False, f"Достигнут лимит найма ({MAX_HIRED_DRONES}/{MAX_HIRED_DRONES})"
        
        # Проверка наличия свободных дронов
        key = f"{drone_type}_lvl{level}"
        available = drones_data.get(key, 0)
        
        # Свободные = всего - в найме (упрощённо, считаем что все в ангаре свободны)
        if available < count:
            return False, f"Недостаточно свободных дронов. Доступно: {available}"
        
        # Проверка слотов
        if count > free_slots:
            return False, f"Недостаточно свободных слотов в найме. Доступно: {free_slots}"
        
        return True, ""
    
    @staticmethod
    def calculate_storage_income(
        drones_data: Dict,
        drones_hired: int,
        last_update: datetime,
        now: datetime = None
    ) -> Dict[str, int]:
        """
        Рассчитать накопленный доход в хранилище
        
        Args:
            drones_data: Dict с количеством дронов
            drones_hired: Количество дронов в найме
            last_update: Время последнего обновления
            now: Текущее время (по умолчанию datetime.now())
            
        Returns:
            Dict с накопленными ресурсами: metal, crystals, dark_matter, minutes_passed
        """
        if now is None:
            now = datetime.now()
        
        if drones_hired == 0:
            return {'metal': 0, 'crystals': 0, 'dark_matter': 0, 'minutes_passed': 0}
        
        # Сколько минут прошло
        minutes_passed = int((now - last_update).total_seconds() / 60)
        
        if minutes_passed <= 0:
            return {'metal': 0, 'crystals': 0, 'dark_matter': 0, 'minutes_passed': 0}
        
        # Доход в минуту
        income_per_minute = DroneSystem.calculate_income_per_minute(drones_data, drones_hired)
        
        return {
            'metal': income_per_minute['metal'] * minutes_passed,
            'crystals': income_per_minute['crystals'] * minutes_passed,
            'dark_matter': income_per_minute['dark_matter'] * minutes_passed,
            'minutes_passed': minutes_passed
        }
    
    @staticmethod
    def check_mission_status(hired_until: Optional[datetime], now: datetime = None) -> Dict:
        """
        Проверить статус миссии дронов
        
        Args:
            hired_until: Время окончания миссии
            now: Текущее время
            
        Returns:
            Dict с ключами: is_active, is_expired, expired_hours_ago
        """
        if now is None:
            now = datetime.now()
        
        if hired_until is None:
            return {'is_active': False, 'is_expired': False, 'expired_hours_ago': 0}
        
        if now < hired_until:
            # Миссия ещё активна
            remaining = int((hired_until - now).total_seconds() / 60)
            return {
                'is_active': True,
                'is_expired': False,
                'remaining_minutes': remaining,
                'expired_hours_ago': 0
            }
        else:
            # Миссия завершена
            hours_ago = (now - hired_until).total_seconds() / 3600
            return {
                'is_active': False,
                'is_expired': True,
                'remaining_minutes': 0,
                'expired_hours_ago': hours_ago
            }
    
    @staticmethod
    def should_clear_storage(hired_until: Optional[datetime], now: datetime = None) -> bool:
        """
        Проверить, нужно ли очистить хранилище (правило 24 часов)
        
        Returns:
            True если прошло более 24 часов после окончания миссии
        """
        status = DroneSystem.check_mission_status(hired_until, now)
        
        if not status['is_expired']:
            return False
        
        # Если прошло более 24 часов
        return status['expired_hours_ago'] >= 24
    
    @staticmethod
    def format_income(income: Dict[str, int]) -> str:
        """
        Форматировать доход для отображения
        
        Args:
            income: Dict с ключами metal, crystals, dark_matter
            
        Returns:
            Строка с эмодзи и значениями
        """
        parts = []
        
        if income.get('metal', 0) > 0:
            parts.append(f"⚙️ {income['metal']:,}")
        if income.get('crystals', 0) > 0:
            parts.append(f"💎 {income['crystals']:,}")
        if income.get('dark_matter', 0) > 0:
            parts.append(f"🕳️ {income['dark_matter']:,}")
        
        return " + ".join(parts) if parts else "0"
    
    @staticmethod
    def format_price(price: Dict[str, int]) -> str:
        """
        Форматировать цену для отображения
        
        Args:
            price: Dict с ключами metal, crystals, dark_matter
            
        Returns:
            Строка с эмодзи и значениями
        """
        parts = []
        
        if price.get('metal', 0) > 0:
            parts.append(f"{price['metal']:,} ⚙️")
        if price.get('crystals', 0) > 0:
            parts.append(f"{price['crystals']:,} 💎")
        if price.get('dark_matter', 0) > 0:
            parts.append(f"{price['dark_matter']:,} 🕳️")
        
        return " + ".join(parts) if parts else "Бесплатно"
