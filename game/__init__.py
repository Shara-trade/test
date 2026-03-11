"""
Игровые механики (скелет)
Пункт3 ТЗ - ИГРОВЫЕ МЕХАНИКИ (ЛОГИКА)
"""

from .mining import MiningSystem
from .energy import EnergySystem
from .heat import HeatSystem, heat_system
from .crit import CritSystem
from .loot import LootSystem, LootItem, Rarity, loot_system
from .drones import DroneSystem
from .modules import ModuleSystem
from .containers import ContainerSystem, ContainerType, ContainerInfo, container_system
from .materials import MaterialSystem, Material, MaterialGroup, material_system
from .expeditions import ExpeditionSystem
from .bosses import BossSystem
from .prestige import PrestigeSystem
from .collections import CollectionSystem
from .craft import CraftSystem
from .seasons import SeasonSystem, Season, SeasonType
from .chat_games import ChatGamesSystem, ChatEvent, ChatEventType
from .economy import EconomySystem, Currency, Price, Transaction
from .levels import LevelSystem, LevelInfo
from .asteroids import AsteroidSystem, AsteroidType, Asteroid, AsteroidSize, asteroid_system

__all__ = [
    'MiningSystem',
    'EnergySystem',
    'HeatSystem',
    'heat_system',
    'CritSystem',
    'LootSystem',
    'LootItem',
    'Rarity',
    'loot_system',
    'DroneSystem',
    'ModuleSystem',
    'ContainerSystem',
    'ContainerType',
    'ContainerInfo',
    'container_system',
    'MaterialSystem',
    'Material',
    'MaterialGroup',
    'material_system',
    'ExpeditionSystem',
    'BossSystem',
    'PrestigeSystem',
    'CollectionSystem',
    'CraftSystem',
    'SeasonSystem',
    'Season',
    'SeasonType',
    'ChatGamesSystem',
    'ChatEvent',
    'ChatEventType',
    'EconomySystem',
    'Currency',
    'Price',
    'Transaction',
    'LevelSystem',
    'LevelInfo',
    'AsteroidSystem',
    'AsteroidType',
    'Asteroid',
    'AsteroidSize',
    'asteroid_system',
]
