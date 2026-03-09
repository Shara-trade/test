"""
3.7. Система модулей (установка и эффекты)
"""
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass


class ModuleType(Enum):
    LASER = 'laser'  # +X к добыче за клик
    BATTERY = 'battery'  # +Y к макс энергии
    SCANNER = 'scanner'  # +Z% к шансу редкого лута
    TURBINE = 'turbine'  # Ускоряет пассивный доход (-0.1 сек)
    COOLING = 'cooling'  # Уменьшает накопление перегрева


@dataclass
class Module:
    """Модель модуля"""
    id: str
    name: str
    module_type: ModuleType
    level: int = 1  # Mk1, Mk2, Mk3
    effect_value: float = 0.0
    rarity: str = 'common'

    # Шаблоны модулей
    TEMPLATES = {
        'laser_mk1': {
            'name': 'Лазерный модуль Mk1',
            'type': ModuleType.LASER,
            'effect': 5,  # +5 к добыче
            'rarity': 'common'
        },
        'laser_mk2': {
            'name': 'Лазерный модуль Mk2',
            'type': ModuleType.LASER,
            'effect': 15,
            'rarity': 'rare'
        },
        'battery_mk1': {
            'name': 'Батарея Mk1',
            'type': ModuleType.BATTERY,
            'effect': 100,  # +100 к макс энергии
            'rarity': 'common'
        },
        'scanner_mk1': {
            'name': 'Сканер Mk1',
            'type': ModuleType.SCANNER,
            'effect': 0.02,  # +2% к шансу лута
            'rarity': 'common'
        },
        'turbine_mk1': {
            'name': 'Турбина Mk1',
            'type': ModuleType.TURBINE,
            'effect': 0.1,  # -0.1 сек к тику
            'rarity': 'rare'
        },
        'cooling_mk1': {
            'name': 'Система охлаждения Mk1',
            'type': ModuleType.COOLING,
            'effect': 2,  # -2% перегрева за клик
            'rarity': 'rare'
        }
    }

    @classmethod
    def create_from_template(cls, template_id: str) -> Optional['Module']:
        """Создать модуль из шаблона"""
        template = cls.TEMPLATES.get(template_id)
        if not template:
            return None

        return cls(
            id=template_id,
            name=template['name'],
            module_type=template['type'],
            effect_value=template['effect'],
            rarity=template['rarity']
        )


class ModuleSystem:
    """Система управления модулями"""

    @staticmethod
    def calculate_total_bonus(modules: List[Module]) -> Dict[str, float]:
        """Расчет суммарных бонусов от всех модулей"""
        bonuses = {
            'mining_bonus': 0,
            'max_energy_bonus': 0,
            'loot_chance_bonus': 0.0,
            'tick_reduction': 0.0,
            'heat_reduction': 0
        }

        for module in modules:
            if module.module_type == ModuleType.LASER:
                bonuses['mining_bonus'] += module.effect_value
            elif module.module_type == ModuleType.BATTERY:
                bonuses['max_energy_bonus'] += module.effect_value
            elif module.module_type == ModuleType.SCANNER:
                bonuses['loot_chance_bonus'] += module.effect_value
            elif module.module_type == ModuleType.TURBINE:
                bonuses['tick_reduction'] += module.effect_value
            elif module.module_type == ModuleType.COOLING:
                bonuses['heat_reduction'] += module.effect_value

        return bonuses

    @staticmethod
    def can_install_module(drone_slots: int, current_modules: int) -> bool:
        """Проверка, можно ли установить модуль"""
        return current_modules < drone_slots

    @staticmethod
    def get_module_description(module: Module) -> str:
        """Получить описание эффекта модуля"""
        descriptions = {
            ModuleType.LASER: f'+{module.effect_value} к добыче за клик',
            ModuleType.BATTERY: f'+{module.effect_value} к макс. энергии',
            ModuleType.SCANNER: f'+{module.effect_value * 100:.0f}% к шансу редкого лута',
            ModuleType.TURBINE: f'-{module.effect_value} сек к интервалу пассивного дохода',
            ModuleType.COOLING: f'-{module.effect_value}% к перегреву за клик'
        }
        return descriptions.get(module.module_type, 'Неизвестный эффект')
