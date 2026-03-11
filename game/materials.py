"""
Система материалов для инвентаря
Согласно Update.txt - 15 материалов в 3 группах
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class MaterialGroup(Enum):
    """Группы материалов"""
    COMMON = "common"      # Обычные (есть во всех контейнерах)
    RARE = "rare"          # Редкие
    EPIC = "epic"          # Эпические (не выпадают из обычных контейнеров)


@dataclass
class Material:
    """Материал для крафта/продажи"""
    key: str
    name: str
    emoji: str
    group: MaterialGroup
    description: str = ""
    base_price: int = 0
    
    # Шансы выпадения по типам контейнеров (0.0 - 1.0)
    drop_chances: Dict[str, float] = None
    
    # Количество при выпадении по типам контейнеров (min, max)
    drop_amounts: Dict[str, tuple] = None
    
    def __post_init__(self):
        if self.drop_chances is None:
            self.drop_chances = {}
        if self.drop_amounts is None:
            self.drop_amounts = {}


class MaterialSystem:
    """Система материалов"""
    
    # Все 15 материалов согласно Update.txt
    MATERIALS: Dict[str, Material] = {}
    
    @classmethod
    def init_materials(cls):
        """Инициализация материалов"""
        
        # ===== ГРУППА 1 - ОБЫЧНЫЕ МАТЕРИАЛЫ =====
        
        cls.MATERIALS["asteroid_rock"] = Material(
            key="asteroid_rock",
            name="Астероидная порода",
            emoji="🪨",
            group=MaterialGroup.COMMON,
            description="Древняя порода из пояса астероидов.",
            base_price=5,
            drop_chances={
                "common": 0.80,
                "rare": 0.90,
                "epic": 0.95,
                "mythic": 1.00,
                "legendary": 1.00,
            },
            drop_amounts={
                "common": (10, 30),
                "rare": (20, 50),
                "epic": (30, 80),
                "mythic": (50, 150),
                "legendary": (100, 300),
            }
        )
        
        cls.MATERIALS["cosmic_silicon"] = Material(
            key="cosmic_silicon",
            name="Космический кремний",
            emoji="🔩",
            group=MaterialGroup.COMMON,
            description="Чистый кремний из космических недр.",
            base_price=8,
            drop_chances={
                "common": 0.60,
                "rare": 0.75,
                "epic": 0.85,
                "mythic": 0.95,
                "legendary": 1.00,
            },
            drop_amounts={
                "common": (5, 15),
                "rare": (10, 30),
                "epic": (20, 50),
                "mythic": (30, 80),
                "legendary": (50, 150),
            }
        )
        
        cls.MATERIALS["metal_fragments"] = Material(
            key="metal_fragments",
            name="Металлические фрагменты",
            emoji="⚙️",
            group=MaterialGroup.COMMON,
            description="Обломки металлических конструкций.",
            base_price=6,
            drop_chances={
                "common": 0.70,
                "rare": 0.80,
                "epic": 0.90,
                "mythic": 0.95,
                "legendary": 1.00,
            },
            drop_amounts={
                "common": (8, 20),
                "rare": (15, 40),
                "epic": (25, 60),
                "mythic": (40, 100),
                "legendary": (80, 200),
            }
        )
        
        cls.MATERIALS["energy_condenser"] = Material(
            key="energy_condenser",
            name="Энергетический конденсатор",
            emoji="⚡",
            group=MaterialGroup.COMMON,
            description="Накапливает и хранит энергию.",
            base_price=15,
            drop_chances={
                "common": 0.40,
                "rare": 0.60,
                "epic": 0.75,
                "mythic": 0.85,
                "legendary": 0.95,
            },
            drop_amounts={
                "common": (2, 8),
                "rare": (5, 15),
                "epic": (10, 30),
                "mythic": (20, 50),
                "legendary": (30, 80),
            }
        )
        
        cls.MATERIALS["quantum_fragment"] = Material(
            key="quantum_fragment",
            name="Квантовый фрагмент",
            emoji="💫",
            group=MaterialGroup.COMMON,
            description="Частица квантового поля.",
            base_price=25,
            drop_chances={
                "common": 0.20,
                "rare": 0.40,
                "epic": 0.60,
                "mythic": 0.75,
                "legendary": 0.90,
            },
            drop_amounts={
                "common": (1, 4),
                "rare": (3, 10),
                "epic": (5, 20),
                "mythic": (10, 30),
                "legendary": (15, 50),
            }
        )
        
        # ===== ГРУППА 2 - РЕДКИЕ МАТЕРИАЛЫ =====
        
        cls.MATERIALS["xenotissue"] = Material(
            key="xenotissue",
            name="Ксеноткань",
            emoji="🧬",
            group=MaterialGroup.RARE,
            description="Органическая ткань инопланетного происхождения.",
            base_price=50,
            drop_chances={
                "common": 0.05,
                "rare": 0.20,
                "epic": 0.40,
                "mythic": 0.60,
                "legendary": 0.80,
            },
            drop_amounts={
                "common": (1, 2),
                "rare": (2, 5),
                "epic": (3, 8),
                "mythic": (5, 15),
                "legendary": (10, 25),
            }
        )
        
        cls.MATERIALS["plasma_core"] = Material(
            key="plasma_core",
            name="Плазменное ядро",
            emoji="☄️",
            group=MaterialGroup.RARE,
            description="Стабилизированное плазменное образование.",
            base_price=80,
            drop_chances={
                "common": 0.03,
                "rare": 0.15,
                "epic": 0.35,
                "mythic": 0.55,
                "legendary": 0.75,
            },
            drop_amounts={
                "common": (1, 1),
                "rare": (1, 3),
                "epic": (2, 6),
                "mythic": (4, 12),
                "legendary": (8, 20),
            }
        )
        
        cls.MATERIALS["astral_crystal"] = Material(
            key="astral_crystal",
            name="Астральный кристалл",
            emoji="🔮",
            group=MaterialGroup.RARE,
            description="Кристалл с астральной энергией.",
            base_price=100,
            drop_chances={
                "common": 0.02,
                "rare": 0.12,
                "epic": 0.30,
                "mythic": 0.50,
                "legendary": 0.70,
            },
            drop_amounts={
                "common": (1, 1),
                "rare": (1, 3),
                "epic": (2, 5),
                "mythic": (3, 10),
                "legendary": (6, 18),
            }
        )
        
        cls.MATERIALS["gravity_node"] = Material(
            key="gravity_node",
            name="Гравитационный узел",
            emoji="🌀",
            group=MaterialGroup.RARE,
            description="Узел гравитационных сил.",
            base_price=150,
            drop_chances={
                "common": 0.01,
                "rare": 0.10,
                "epic": 0.25,
                "mythic": 0.45,
                "legendary": 0.65,
            },
            drop_amounts={
                "common": (1, 1),
                "rare": (1, 2),
                "epic": (1, 4),
                "mythic": (2, 8),
                "legendary": (4, 15),
            }
        )
        
        cls.MATERIALS["antimatter_capsule"] = Material(
            key="antimatter_capsule",
            name="Антиматериальная капсула",
            emoji="🧪",
            group=MaterialGroup.RARE,
            description="Капсула с антиматерией.",
            base_price=250,
            drop_chances={
                "common": 0.005,
                "rare": 0.08,
                "epic": 0.20,
                "mythic": 0.40,
                "legendary": 0.60,
            },
            drop_amounts={
                "common": (1, 1),
                "rare": (1, 1),
                "epic": (1, 3),
                "mythic": (2, 6),
                "legendary": (3, 12),
            }
        )
        
        # ===== ГРУППА 3 - ЭПИЧЕСКИЕ МАТЕРИАЛЫ =====
        
        cls.MATERIALS["star_dust"] = Material(
            key="star_dust",
            name="Звёздная пыль",
            emoji="✨",
            group=MaterialGroup.EPIC,
            description="Пыль от погибших звёзд.",
            base_price=500,
            drop_chances={
                "common": 0.00,
                "rare": 0.05,
                "epic": 0.15,
                "mythic": 0.30,
                "legendary": 0.50,
            },
            drop_amounts={
                "common": (0, 0),
                "rare": (1, 1),
                "epic": (1, 3),
                "mythic": (2, 5),
                "legendary": (3, 10),
            }
        )
        
        cls.MATERIALS["ion_module"] = Material(
            key="ion_module",
            name="Ионный модуль",
            emoji="⚡",
            group=MaterialGroup.EPIC,
            description="Продвинутый ионный модуль.",
            base_price=600,
            drop_chances={
                "common": 0.00,
                "rare": 0.04,
                "epic": 0.12,
                "mythic": 0.25,
                "legendary": 0.45,
            },
            drop_amounts={
                "common": (0, 0),
                "rare": (1, 1),
                "epic": (1, 2),
                "mythic": (1, 4),
                "legendary": (2, 8),
            }
        )
        
        cls.MATERIALS["ancient_nav_chip"] = Material(
            key="ancient_nav_chip",
            name="Древний навигационный чип",
            emoji="🛸",
            group=MaterialGroup.EPIC,
            description="Чип навигации древней цивилизации.",
            base_price=800,
            drop_chances={
                "common": 0.00,
                "rare": 0.03,
                "epic": 0.10,
                "mythic": 0.20,
                "legendary": 0.40,
            },
            drop_amounts={
                "common": (0, 0),
                "rare": (1, 1),
                "epic": (1, 1),
                "mythic": (1, 3),
                "legendary": (2, 6),
            }
        )
        
        cls.MATERIALS["protoplanet_fragment"] = Material(
            key="protoplanet_fragment",
            name="Фрагмент протопланеты",
            emoji="🪐",
            group=MaterialGroup.EPIC,
            description="Осколок древней протопланеты.",
            base_price=1000,
            drop_chances={
                "common": 0.00,
                "rare": 0.02,
                "epic": 0.08,
                "mythic": 0.15,
                "legendary": 0.35,
            },
            drop_amounts={
                "common": (0, 0),
                "rare": (1, 1),
                "epic": (1, 1),
                "mythic": (1, 2),
                "legendary": (1, 5),
            }
        )
        
        cls.MATERIALS["supernova_shard"] = Material(
            key="supernova_shard",
            name="Осколок сверхновой",
            emoji="🌟",
            group=MaterialGroup.EPIC,
            description="Осколок взорвавшейся звезды.",
            base_price=2000,
            drop_chances={
                "common": 0.00,
                "rare": 0.01,
                "epic": 0.05,
                "mythic": 0.10,
                "legendary": 0.25,
            },
            drop_amounts={
                "common": (0, 0),
                "rare": (1, 1),
                "epic": (1, 1),
                "mythic": (1, 1),
                "legendary": (1, 3),
            }
        )
    
    @classmethod
    def get_material(cls, key: str) -> Optional[Material]:
        """Получить материал по ключу"""
        return cls.MATERIALS.get(key)
    
    @classmethod
    def get_all_materials(cls) -> List[Material]:
        """Получить все материалы в порядке отображения"""
        order = [
            # Группа 1 - Обычные
            "asteroid_rock",
            "cosmic_silicon", 
            "metal_fragments",
            "energy_condenser",
            "quantum_fragment",
            # Группа 2 - Редкие
            "xenotissue",
            "plasma_core",
            "astral_crystal",
            "gravity_node",
            "antimatter_capsule",
            # Группа 3 - Эпические
            "star_dust",
            "ion_module",
            "ancient_nav_chip",
            "protoplanet_fragment",
            "supernova_shard",
        ]
        return [cls.MATERIALS[key] for key in order if key in cls.MATERIALS]
    
    @classmethod
    def get_materials_by_group(cls, group: MaterialGroup) -> List[Material]:
        """Получить материалы по группе"""
        return [m for m in cls.MATERIALS.values() if m.group == group]


# Инициализация при импорте
MaterialSystem.init_materials()

# Глобальный экземпляр
material_system = MaterialSystem()
