"""
3.3. Система перегрева (Heat)
"""
import time
import random
from typing import Dict, Tuple
from collections import deque
from dataclasses import dataclass


@dataclass
class HeatInfo:
    """Информация о перегреве"""
    current_heat: int
    max_heat: int
    bonus_multiplier: float
    is_overheated: bool
    cooldown_seconds: int


class HeatSystem:
    """Система перегрева буров"""

    # Параметры системы
    MAX_HEAT = 100
    HEAT_PER_CLICK_MIN = 2
    HEAT_PER_CLICK_MAX = 5
    
    # Пороги скорости кликов
    FAST_CLICK_THRESHOLD = 1.0      # < 1 сек между кликами
    VERY_FAST_CLICK_THRESHOLD = 0.5  # < 0.5 сек между кликами
    
    # Дополнительный перегрев за быстрые клики
    FAST_CLICK_HEAT = 5
    VERY_FAST_CLICK_HEAT = 10
    
    # Остывание
    COOLDOWN_PER_SECOND = 1
    
    # Блокировка при перегреве
    OVERHEAT_THRESHOLD = 100
    OVERHEAT_PENALTY_SECONDS = 5

    # Бонус перегрева
    HEAT_BONUS_THRESHOLD = 80  # При каком перегреве начинает действовать бонус
    MAX_HEAT_BONUS = 1.5       # Максимальный множитель бонуса

    def __init__(self):
        self.click_history: Dict[int, deque] = {}

    def get_click_heat_increase(self, user_id: int, click_interval: float = None) -> int:
        """
        Расчет прироста перегрева за клик.
        
        Args:
            user_id: ID пользователя
            click_interval: Интервал с предыдущего клика (опционально)
        """
        # Базовый перегрев
        heat = random.randint(self.HEAT_PER_CLICK_MIN, self.HEAT_PER_CLICK_MAX)
        
        # Если интервал не передан, рассчитываем из истории
        if click_interval is None:
            click_interval = self._get_last_interval(user_id)
        
        # Дополнительный перегрев за быстрые клики
        if click_interval is not None:
            if click_interval < self.VERY_FAST_CLICK_THRESHOLD:
                heat += self.VERY_FAST_CLICK_HEAT
            elif click_interval < self.FAST_CLICK_THRESHOLD:
                heat += self.FAST_CLICK_HEAT
        
        return heat

    def _get_last_interval(self, user_id: int) -> float:
        """Получить интервал с последнего клика"""
        if user_id not in self.click_history or len(self.click_history[user_id]) < 2:
            return None
        
        clicks = list(self.click_history[user_id])
        return clicks[-1] - clicks[-2]

    def record_click(self, user_id: int) -> float:
        """
        Записать клик и вернуть интервал.
        
        Returns:
            Интервал в секундах или None
        """
        now = time.time()
        
        if user_id not in self.click_history:
            self.click_history[user_id] = deque(maxlen=100)
        
        clicks = self.click_history[user_id]
        
        interval = None
        if clicks:
            interval = now - clicks[-1]
        
        clicks.append(now)
        
        return interval

    def _calculate_speed_bonus(self, user_id: int) -> int:
        """Расчет бонуса перегрева от скорости кликов"""
        if user_id not in self.click_history:
            return 0

        now = time.time()
        recent_clicks = sum(1 for t in self.click_history[user_id] if now - t <= 10)

        if recent_clicks > 10:
            return 10
        elif recent_clicks > 5:
            return 5
        return 0

    @staticmethod
    def is_overheated(current_heat: int) -> bool:
        """Проверка, перегреты ли буры"""
        return current_heat >= HeatSystem.OVERHEAT_THRESHOLD

    @staticmethod
    def calculate_bonus(heat: int) -> float:
        """
        Рассчитать бонус к добыче от перегрева.
        
        Бонус начинает действовать при heat >= 80
        Максимальный бонус = 1.5x при heat = 100
        """
        if heat < HeatSystem.HEAT_BONUS_THRESHOLD:
            return 1.0
        
        # Линейная интерполяция от 80 до 100
        bonus_range = HeatSystem.MAX_HEAT - HeatSystem.HEAT_BONUS_THRESHOLD
        heat_above_threshold = heat - HeatSystem.HEAT_BONUS_THRESHOLD
        
        bonus = 1.0 + ((HeatSystem.MAX_HEAT_BONUS - 1.0) * (heat_above_threshold / bonus_range))
        
        return min(HeatSystem.MAX_HEAT_BONUS, bonus)

    @staticmethod
    def get_heat_multiplier(heat_percent: float) -> float:
        """Множитель добычи от перегрева (до x1.5 при 80%)"""
        if heat_percent <= 80:
            return 1 + (heat_percent / 100 * 0.5)
        return HeatSystem.MAX_HEAT_BONUS

    @staticmethod
    def cooldown(current_heat: int, seconds: int = 1) -> int:
        """Остывание буров"""
        return max(0, current_heat - (HeatSystem.COOLDOWN_PER_SECOND * seconds))

    @staticmethod
    def get_heat_info(heat: int) -> HeatInfo:
        """Получить полную информацию о перегреве"""
        return HeatInfo(
            current_heat=heat,
            max_heat=HeatSystem.MAX_HEAT,
            bonus_multiplier=HeatSystem.calculate_bonus(heat),
            is_overheated=heat >= HeatSystem.MAX_HEAT,
            cooldown_seconds=HeatSystem.OVERHEAT_PENALTY_SECONDS if heat >= HeatSystem.MAX_HEAT else 0
        )

    @staticmethod
    def format_heat_bar(heat: int, width: int = 10) -> str:
        """Форматировать полоску перегрева"""
        percent = (heat / HeatSystem.MAX_HEAT) * 100
        filled = int(percent / (100 / width))
        empty = width - filled
        
        # Цвет в зависимости от уровня
        if heat < 50:
            char = "🟩"
        elif heat < 80:
            char = "🟨"
        else:
            char = "🟥"
        
        return char * filled + "⬜" * empty

    def get_clicks_in_window(self, user_id: int, window_seconds: float = 10.0) -> int:
        """Получить количество кликов за последнее время"""
        if user_id not in self.click_history:
            return 0
        
        now = time.time()
        cutoff = now - window_seconds
        
        return sum(1 for t in self.click_history[user_id] if t > cutoff)

    def clear_old_clicks(self, user_id: int, max_age: float = 60.0):
        """Очистить старые клики"""
        if user_id not in self.click_history:
            return
        
        now = time.time()
        cutoff = now - max_age
        
        self.click_history[user_id] = deque(
            [t for t in self.click_history[user_id] if t > cutoff],
            maxlen=100
        )


# Глобальный экземпляр
heat_system = HeatSystem()
