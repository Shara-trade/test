"""
3.15. Крафт и синтез
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class RecipeType(Enum):
    MODULE = 'module'  # Модули
    DRONE = 'drone'  # Дроны
    ARTIFACT = 'artifact'  # Артефакты
    UPGRADE = 'upgrade'  # Улучшения


@dataclass
class Recipe:
    """Рецепт крафта"""
    id: str
    name: str
    recipe_type: RecipeType
    rarity: str
    ingredients: Dict[str, int]  # {item_id: count} или {resource: count}
    result_item: str

    RECIPES = {
        # Модули
        'laser_mk2': {
            'name': 'Лазерный модуль Mk2',
            'type': RecipeType.MODULE,
            'rarity': 'rare',
            'ingredients': {
                'laser_mk1': 3,
                'metal': 1000,
                'crystals': 50
            },
            'result': 'laser_mk2'
        },
        'battery_mk2': {
            'name': 'Батарея Mk2',
            'type': RecipeType.MODULE,
            'rarity': 'rare',
            'ingredients': {
                'battery_mk1': 3,
                'metal': 800,
                'crystals': 40
            },
            'result': 'battery_mk2'
        },
        'quantum_module': {
            'name': 'Квантовый модуль',
            'type': RecipeType.MODULE,
            'rarity': 'epic',
            'ingredients': {
                'laser_mk2': 2,
                'battery_mk2': 2,
                'dark_matter': 10
            },
            'result': 'quantum_module'
        },

        # Дроны
        'miner_drone': {
            'name': 'Шахтёр (дрон)',
            'type': RecipeType.DRONE,
            'rarity': 'common',
            'ingredients': {
                'metal': 500,
                'crystals': 20,
                'basic_drone_blueprint': 1
            },
            'result': 'miner_drone'
        },
        'laser_drone': {
            'name': 'Лазерный дрон',
            'type': RecipeType.DRONE,
            'rarity': 'rare',
            'ingredients': {
                'metal': 2500,
                'crystals': 100,
                'laser_drone_blueprint': 1
            },
            'result': 'laser_drone'
        },
        'ai_drone': {
            'name': 'ИИ-дрон',
            'type': RecipeType.DRONE,
            'rarity': 'legendary',
            'ingredients': {
                'metal': 50000,
                'crystals': 100,
                'dark_matter': 5,
                'ai_core': 1
            },
            'result': 'ai_drone'
        },

        # Артефакты
        'ai_core': {
            'name': 'Ядро ИИ',
            'type': RecipeType.ARTIFACT,
            'rarity': 'rare',
            'ingredients': {
                'ancient_engine': 2,
                'crystals': 500,
                'metal': 5000
            },
            'result': 'ai_core'
        },
        'ancient_engine': {
            'name': 'Древний двигатель',
            'type': RecipeType.ARTIFACT,
            'rarity': 'epic',
            'ingredients': {
                'rare_parts': 5,
                'crystals': 200,
                'metal': 2000
            },
            'result': 'ancient_engine'
        }
    }


class CraftSystem:
    """Система крафта"""

    @staticmethod
    def get_recipe(recipe_id: str) -> Optional[Dict]:
        """Получить рецепт по ID"""
        return Recipe.RECIPES.get(recipe_id)

    @staticmethod
    def can_craft(recipe_id: str, user_resources: Dict[str, int],
                  user_items: Dict[str, int]) -> tuple[bool, List[str]]:
        """
        Проверка, можно ли скрафтить предмет

        Returns:
            (можно_ли, список_недостающего)
        """
        recipe = CraftSystem.get_recipe(recipe_id)
        if not recipe:
            return False, ['Рецепт не найден']

        missing = []
        ingredients = recipe['ingredients']

        for item_id, required_count in ingredients.items():
            # Проверяем ресурсы
            if item_id in ['metal', 'crystals', 'dark_matter']:
                if user_resources.get(item_id, 0) < required_count:
                    missing.append(f"{item_id}: {user_resources.get(item_id, 0)}/{required_count}")
            else:
                # Проверяем предметы
                if user_items.get(item_id, 0) < required_count:
                    missing.append(f"{item_id}: {user_items.get(item_id, 0)}/{required_count}")

        return len(missing) == 0, missing

    @staticmethod
    def get_max_craft_count(recipe_id: str, user_resources: Dict[str, int],
                            user_items: Dict[str, int]) -> int:
        """Сколько раз можно скрафтить предмет"""
        recipe = CraftSystem.get_recipe(recipe_id)
        if not recipe:
            return 0

        max_count = float('inf')
        ingredients = recipe['ingredients']

        for item_id, required_count in ingredients.items():
            if item_id in ['metal', 'crystals', 'dark_matter']:
                available = user_resources.get(item_id, 0)
            else:
                available = user_items.get(item_id, 0)

            possible = available // required_count
            max_count = min(max_count, possible)

        return int(max_count) if max_count != float('inf') else 0

    @staticmethod
    def get_recipes_by_type(recipe_type: RecipeType) -> Dict[str, Dict]:
        """Получить все рецепты определенного типа"""
        return {
            k: v for k, v in Recipe.RECIPES.items()
            if v['type'] == recipe_type
        }

    @staticmethod
    def get_available_recipes(user_resources: Dict[str, int],
                              user_items: Dict[str, int]) -> List[str]:
        """Получить список доступных для крафта рецептов"""
        available = []
        for recipe_id in Recipe.RECIPES:
            can_craft, _ = CraftSystem.can_craft(recipe_id, user_resources, user_items)
            if can_craft:
                available.append(recipe_id)
        return available
