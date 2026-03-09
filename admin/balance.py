"""
5.11. Балансировка
Изменение параметров игры на лету
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
import json


@dataclass
class GameParameter:
    """Игровой параметр"""
    key: str
    name: str
    description: str
    value: Any
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    value_type: str = "float"  # float, int, bool, string
    category: str = "general"
    
    def validate(self, new_value: Any) -> tuple:
        """Валидация нового значения"""
        try:
            # Приведение типа
            if self.value_type == "int":
                new_value = int(new_value)
            elif self.value_type == "float":
                new_value = float(new_value)
            elif self.value_type == "bool":
                if isinstance(new_value, str):
                    new_value = new_value.lower() in ("true", "1", "yes")
                new_value = bool(new_value)
            
            # Проверка границ
            if self.min_value is not None and new_value < self.min_value:
                return False, f"Значение меньше минимума ({self.min_value})"
            
            if self.max_value is not None and new_value > self.max_value:
                return False, f"Значение больше максимума ({self.max_value})"
            
            return True, new_value
            
        except (ValueError, TypeError) as e:
            return False, f"Неверный тип данных: {e}"


class BalanceManager:
    """Менеджер балансировки"""
    
    # Категории параметров
    CATEGORIES = {
        "mining": "⛏ Добыча",
        "energy": "⚡ Энергия",
        "heat": "🌡 Перегрев",
        "crit": "💥 Криты",
        "loot": "📦 Лут",
        "drones": "🤖 Дроны",
        "economy": "💰 Экономика",
        "containers": "📦 Контейнеры",
        "expeditions": "🚀 Экспедиции",
        "bosses": "👾 Боссы",
    }
    
    # Игровые параметры по умолчанию
    DEFAULT_PARAMS = {
        # Добыча
        "mining_base_amount": GameParameter(
            key="mining_base_amount",
            name="Базовая добыча",
            description="Базовое количество металла за клик",
            value=10,
            min_value=1,
            max_value=1000,
            value_type="int",
            category="mining"
        ),
        "mining_crystal_ratio": GameParameter(
            key="mining_crystal_ratio",
            name="Коэффициент кристаллов",
            description="Доля кристаллов от добычи металла",
            value=0.1,
            min_value=0.0,
            max_value=1.0,
            value_type="float",
            category="mining"
        ),
        "mining_dark_matter_chance": GameParameter(
            key="mining_dark_matter_chance",
            name="Шанс тёмной материи",
            description="Шанс получения тёмной материи за клик",
            value=0.01,
            min_value=0.0,
            max_value=1.0,
            value_type="float",
            category="mining"
        ),
        
        # Энергия
        "energy_cost_per_click": GameParameter(
            key="energy_cost_per_click",
            name="Стоимость клика",
            description="Энергии за один клик",
            value=10,
            min_value=1,
            max_value=100,
            value_type="int",
            category="energy"
        ),
        "energy_regen_per_minute": GameParameter(
            key="energy_regen_per_minute",
            name="Восстановление в минуту",
            description="Энергии восстанавливается в минуту",
            value=5,
            min_value=1,
            max_value=100,
            value_type="int",
            category="energy"
        ),
        "energy_max_base": GameParameter(
            key="energy_max_base",
            name="Базовая макс. энергия",
            description="Максимальная энергия без бонусов",
            value=1000,
            min_value=100,
            max_value=10000,
            value_type="int",
            category="energy"
        ),
        "energy_per_level": GameParameter(
            key="energy_per_level",
            name="Энергия за уровень",
            description="Дополнительная энергия за уровень",
            value=50,
            min_value=0,
            max_value=500,
            value_type="int",
            category="energy"
        ),
        
        # Перегрев
        "heat_per_click_min": GameParameter(
            key="heat_per_click_min",
            name="Мин. перегрев за клик",
            description="Минимальный перегрев за клик",
            value=2,
            min_value=0,
            max_value=20,
            value_type="int",
            category="heat"
        ),
        "heat_per_click_max": GameParameter(
            key="heat_per_click_max",
            name="Макс. перегрев за клик",
            description="Максимальный перегрев за клик",
            value=5,
            min_value=0,
            max_value=20,
            value_type="int",
            category="heat"
        ),
        "heat_cooldown_per_sec": GameParameter(
            key="heat_cooldown_per_sec",
            name="Остывание в секунду",
            description="Насколько остывает в секунду",
            value=1,
            min_value=0,
            max_value=10,
            value_type="int",
            category="heat"
        ),
        "heat_max": GameParameter(
            key="heat_max",
            name="Макс. перегрев",
            description="При каком перегреве блокировка",
            value=100,
            min_value=50,
            max_value=200,
            value_type="int",
            category="heat"
        ),
        "heat_bonus_max": GameParameter(
            key="heat_bonus_max",
            name="Макс. бонус перегрева",
            description="Максимальный множитель от перегрева",
            value=1.5,
            min_value=1.0,
            max_value=3.0,
            value_type="float",
            category="heat"
        ),
        
        # Криты
        "crit_base_chance": GameParameter(
            key="crit_base_chance",
            name="Базовый шанс крита",
            description="Шанс критического удара",
            value=0.02,
            min_value=0.0,
            max_value=1.0,
            value_type="float",
            category="crit"
        ),
        "crit_x2_multiplier": GameParameter(
            key="crit_x2_multiplier",
            name="Множитель крита x2",
            description="Множитель обычного крита",
            value=2,
            min_value=1,
            max_value=10,
            value_type="int",
            category="crit"
        ),
        "crit_x5_multiplier": GameParameter(
            key="crit_x5_multiplier",
            name="Множитель крита x5",
            description="Множитель редкого крита",
            value=5,
            min_value=1,
            max_value=20,
            value_type="int",
            category="crit"
        ),
        "crit_x10_multiplier": GameParameter(
            key="crit_x10_multiplier",
            name="Множитель крита x10",
            description="Множитель эпического крита",
            value=10,
            min_value=1,
            max_value=50,
            value_type="int",
            category="crit"
        ),
        
        # Лут
        "loot_drop_chance": GameParameter(
            key="loot_drop_chance",
            name="Шанс выпадения предмета",
            description="Базовый шанс выпадения предмета",
            value=0.03,
            min_value=0.0,
            max_value=1.0,
            value_type="float",
            category="loot"
        ),
        
        # Дроны
        "drone_tick_interval": GameParameter(
            key="drone_tick_interval",
            name="Интервал сбора дронов",
            description="Секунды между сбором дохода",
            value=5,
            min_value=1,
            max_value=60,
            value_type="int",
            category="drones"
        ),
        "drone_max_count": GameParameter(
            key="drone_max_count",
            name="Макс. дронов",
            description="Максимальное количество дронов",
            value=50,
            min_value=1,
            max_value=500,
            value_type="int",
            category="drones"
        ),
        "drone_max_level": GameParameter(
            key="drone_max_level",
            name="Макс. уровень дрона",
            description="Максимальный уровень улучшения",
            value=10,
            min_value=1,
            max_value=100,
            value_type="int",
            category="drones"
        ),
        
        # Экономика
        "market_commission": GameParameter(
            key="market_commission",
            name="Комиссия рынка",
            description="Процент комиссии при продаже",
            value=0.05,
            min_value=0.0,
            max_value=0.5,
            value_type="float",
            category="economy"
        ),
        "starter_credits": GameParameter(
            key="starter_credits",
            name="Стартовые кредиты",
            description="Кредиты при регистрации",
            value=1000,
            min_value=0,
            max_value=10000,
            value_type="int",
            category="economy"
        ),
        
        # Контейнеры
        "container_drop_chance": GameParameter(
            key="container_drop_chance",
            name="Шанс выпадения контейнера",
            description="Шанс выпадения при клике",
            value=0.02,
            min_value=0.0,
            max_value=1.0,
            value_type="float",
            category="containers"
        ),
        "container_common_time": GameParameter(
            key="container_common_time",
            name="Время обычного контейнера",
            description="Минуты до открытия",
            value=5,
            min_value=1,
            max_value=60,
            value_type="int",
            category="containers"
        ),
        "container_rare_time": GameParameter(
            key="container_rare_time",
            name="Время редкого контейнера",
            description="Минуты до открытия",
            value=30,
            min_value=1,
            max_value=180,
            value_type="int",
            category="containers"
        ),
        "container_epic_time": GameParameter(
            key="container_epic_time",
            name="Время эпического контейнера",
            description="Минуты до открытия",
            value=120,
            min_value=1,
            max_value=480,
            value_type="int",
            category="containers"
        ),
    }
    
    def __init__(self):
        self.params = self.DEFAULT_PARAMS.copy()
    
    def get_param(self, key: str) -> Optional[GameParameter]:
        """Получить параметр"""
        return self.params.get(key)
    
    def get_all_params(self) -> Dict[str, GameParameter]:
        """Получить все параметры"""
        return self.params
    
    def get_params_by_category(self, category: str) -> Dict[str, GameParameter]:
        """Получить параметры по категории"""
        return {
            k: v for k, v in self.params.items()
            if v.category == category
        }
    
    def set_param(self, key: str, value: Any, admin_id: int) -> tuple:
        """Установить новое значение параметра"""
        param = self.params.get(key)
        if not param:
            return False, f"Параметр {key} не найден"
        
        valid, result = param.validate(value)
        if not valid:
            return False, result
        
        old_value = param.value
        param.value = result
        
        return True, {
            "key": key,
            "old_value": old_value,
            "new_value": result,
            "admin_id": admin_id
        }
    
    def export_to_json(self) -> str:
        """Экспорт параметров в JSON"""
        data = {}
        for key, param in self.params.items():
            data[key] = {
                "value": param.value,
                "name": param.name,
                "category": param.category
            }
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def import_from_json(self, json_data: str) -> tuple:
        """Импорт параметров из JSON"""
        try:
            data = json.loads(json_data)
            updated = 0
            
            for key, values in data.items():
                if key in self.params:
                    param = self.params[key]
                    param.value = values.get("value", param.value)
                    updated += 1
            
            return True, f"Обновлено параметров: {updated}"
            
        except Exception as e:
            return False, f"Ошибка импорта: {e}"
    
    def format_category_params(self, category: str) -> str:
        """Форматировать параметры категории для отображения"""
        params = self.get_params_by_category(category)
        category_name = self.CATEGORIES.get(category, category)
        
        text = f"{category_name}\n\n"
        
        for key, param in params.items():
            text += f"▸ {param.name}: {param.value}\n"
        
        return text
