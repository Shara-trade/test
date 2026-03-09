"""
3.3. Система перегрева (Heat)
"""
import time
import random
from typing import Dict
from collections import deque


class HeatSystem:
    """Система перегрева буров"""

    COOLDOWN_PER_SECOND = 1
    OVERHEAT_THRESHOLD = 100
    OVERHEAT_PENALTY_SECONDS = 5

    def __init__(self):
        self.click_history: Dict[int, deque] = {}

    def get_click_heat_increase(self, user_id: int) -> int:
        """Расчет прироста перегрева за клик"""
        base_increase = random.randint(2, 5)
        speed_bonus = self._calculate_speed_bonus(user_id)
        return base_increase + speed_bonus

    def _calculate_speed_bonus(self, user_id: int) -> int:
        """Расчет бонуса перегрева от скорости кликов"""
        if user_id not in self.click_history:
            self.click_history[user_id] = deque(maxlen=20)

        now = time.time()
        self.click_history[user_id].append(now)

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
    def get_heat_multiplier(heat_percent: float) -> float:
        """Множитель добычи от перегрева (до x1.5 при 80%)"""
        if heat_percent <= 80:
            return 1 + (heat_percent / 100 * 0.5)
        return 1.0

    @staticmethod
    def cooldown(current_heat: int, seconds: int = 1) -> int:
        """Остывание буров"""
        return max(0, current_heat - (HeatSystem.COOLDOWN_PER_SECOND * seconds))
