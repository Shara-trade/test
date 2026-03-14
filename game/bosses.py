"""
3.13. Система боссов (личных и клановых)
"""
import random
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class BossType(Enum):
    PERSONAL = 'personal'  # Личный босс
    CLAN = 'clan'  # Клановый босс


class BossRarity(Enum):
    COMMON = 'common'
    RARE = 'rare'
    EPIC = 'epic'
    LEGENDARY = 'legendary'


@dataclass
class Boss:
    """Модель босса"""
    id: int
    name: str
    boss_type: BossType
    rarity: BossRarity
    level: int
    hp: int
    max_hp: int
    damage_per_click: int = 10

    BOSSES = {
        'space_worm': {
            'name': '🐛 Космический червь',
            'rarity': BossRarity.COMMON,
            'base_hp': 1000,
            'damage_per_click': 10,
            'rewards': {'metal': 1000, 'crystals': 100}
        },
        'asteroid_golem': {
            'name': '🗿 Астероидный голем',
            'rarity': BossRarity.RARE,
            'base_hp': 5000,
            'damage_per_click': 25,
            'rewards': {'metal': 5000, 'crystals': 500, 'item': True}
        },
        'void_leviathan': {
            'name': '🦑 Пустотный левиафан',
            'rarity': BossRarity.EPIC,
            'base_hp': 20000,
            'damage_per_click': 50,
            'rewards': {'metal': 20000, 'crystals': 2000, 'dark_matter': 50, 'item': True}
        },
        'galaxy_devourer': {
            'name': '🌌 Пожиратель галактик',
            'rarity': BossRarity.LEGENDARY,
            'base_hp': 100000,
            'damage_per_click': 100,
            'rewards': {'metal': 100000, 'crystals': 10000, 'dark_matter': 500, 'legendary_item': True}
        }
    }

    @classmethod
    def create_boss(cls, boss_key: str, boss_type: BossType, level: int = 1) -> Optional['Boss']:
        """Создать босса по ключу"""
        template = cls.BOSSES.get(boss_key)
        if not template:
            return None

        # Масштабирование ХП по уровню
        hp_multiplier = 1 + (level - 1) * 0.5
        max_hp = int(template['base_hp'] * hp_multiplier)

        return cls(
            id=random.randint(1000, 9999),
            name=template['name'],
            boss_type=boss_type,
            rarity=template['rarity'],
            level=level,
            hp=max_hp,
            max_hp=max_hp,
            damage_per_click=template['damage_per_click']
        )


class BossSystem:
    """Система боссов"""

    PERSONAL_BOSS_COOLDOWN = 360  # 6 часов в минутах
    CLAN_BOSS_RESPAWN = 720  # 12 часов в минутах

    @staticmethod
    def calculate_damage(
        user_clicks: int,
        drone_power: int,
        modules_bonus: int
    ) -> int:
        """Расчет урона по боссу"""
        base_damage = user_clicks * 10
        drone_damage = drone_power * 5
        return base_damage + drone_damage + modules_bonus

    @staticmethod
    def is_defeated(boss: Boss) -> bool:
        """Проверка, побежден ли босс"""
        return boss.hp <= 0

    @staticmethod
    def get_defeat_rewards(boss: Boss) -> Dict:
        """Получить награды за победу над боссом"""
        template = Boss.BOSSES.get(boss.name.lower().replace(' ', '_'))
        if not template:
            return {'metal': 100, 'crystals': 10}

        rewards = template['rewards'].copy()

        # Добавляем случайный предмет если нужно
        if rewards.get('item'):
            rewards['item'] = {'name': 'Редкий предмет с босса', 'rarity': 'rare'}
        if rewards.get('legendary_item'):
            rewards['legendary_item'] = {'name': 'Легендарный артефакт', 'rarity': 'legendary'}

        return rewards

    @staticmethod
    def get_spawn_chance() -> float:
        """Шанс появления личного босса (при клике)"""
        return 0.001  # 0.1% шанс

    @staticmethod
    def can_fight_personal_boss(last_fight_time: Optional[datetime]) -> bool:
        """Проверка, прошло ли достаточно времени с последнего боя"""
        if not last_fight_time:
            return True

        cooldown = timedelta(minutes=BossSystem.PERSONAL_BOSS_COOLDOWN)
        return datetime.now() >= last_fight_time + cooldown
