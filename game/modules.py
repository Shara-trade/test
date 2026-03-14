"""
Система модулей
Согласно module.txt - генерация модулей с бафами и дебафами
"""
import random
import json
from typing import Dict, List, Optional, Tuple
from enum import IntEnum
from dataclasses import dataclass


class Rarity(IntEnum):
    """Редкость модуля (1-5)"""
    COMMON = 1      # ⚪ Обычная
    RARE = 2        # 🟢 Редкая
    EPIC = 3        # 🟣 Эпическая
    MYTHIC = 4      # 🔴 Мифическая
    LEGENDARY = 5   # 🟡 Легендарная


RARITY_EMOJI = {
    Rarity.COMMON: "⚪",
    Rarity.RARE: "🟢",
    Rarity.EPIC: "🟣",
    Rarity.MYTHIC: "🔴",
    Rarity.LEGENDARY: "🟡",
}

RARITY_NAME = {
    Rarity.COMMON: "Обычная",
    Rarity.RARE: "Редкая",
    Rarity.EPIC: "Эпическая",
    Rarity.MYTHIC: "Мифическая",
    Rarity.LEGENDARY: "Легендарная",
}

# Шансы выпадения редкости
RARITY_CHANCES = {
    Rarity.COMMON: 0.70,
    Rarity.RARE: 0.20,
    Rarity.EPIC: 0.07,
    Rarity.MYTHIC: 0.025,
    Rarity.LEGENDARY: 0.005,
}


# ===== БАФЫ (положительные эффекты) =====
BUFF_KEYS = [
    "asteroid_resources",      # Ресурсы с астероида (+%)
    "rare_asteroid_chance",    # Шанс редкого астероида (+%)
    "double_loot_chance",      # Шанс двойной добычи (+%)
    "extra_material_chance",   # Шанс доп. материала (+%)
    "max_energy",              # Макс. энергия (+)
    "energy_regen_speed",      # Скорость регена энергии (+%)
    "heat_reduction",          # Снижение нагрева (-%)
    "drill_cooldown",          # Охлаждение бура (-сек)
    "scrap_bonus",             # Материалы при разборке (+%)
    "container_chance",        # Шанс контейнера (+%)
]

BUFF_NAMES = {
    "asteroid_resources": "Ресурсы с астероида",
    "rare_asteroid_chance": "Шанс редкого астероида",
    "double_loot_chance": "Шанс двойной добычи",
    "extra_material_chance": "Шанс дополнительного материала",
    "max_energy": "Максимальная энергия",
    "energy_regen_speed": "Скорость восстановления энергии",
    "heat_reduction": "Снижение нагрева за клик",
    "drill_cooldown": "Охлаждение бура",
    "scrap_bonus": "Материалы при разборке",
    "container_chance": "Шанс контейнера",
}

# Значения бафов по редкости
BUFF_VALUES = {
    "asteroid_resources": {Rarity.COMMON: 5.5, Rarity.RARE: 7.5, Rarity.EPIC: 9.5, Rarity.MYTHIC: 11.0, Rarity.LEGENDARY: 12.0},
    "rare_asteroid_chance": {Rarity.COMMON: 2.5, Rarity.RARE: 3.5, Rarity.EPIC: 5.0, Rarity.MYTHIC: 6.0, Rarity.LEGENDARY: 7.0},
    "double_loot_chance": {Rarity.COMMON: 3.5, Rarity.RARE: 4.5, Rarity.EPIC: 6.0, Rarity.MYTHIC: 7.0, Rarity.LEGENDARY: 8.0},
    "extra_material_chance": {Rarity.COMMON: 4.5, Rarity.RARE: 6.5, Rarity.EPIC: 8.0, Rarity.MYTHIC: 9.0, Rarity.LEGENDARY: 10.0},
    "max_energy": {Rarity.COMMON: 120, Rarity.RARE: 180, Rarity.EPIC: 230, Rarity.MYTHIC: 270, Rarity.LEGENDARY: 300},
    "energy_regen_speed": {Rarity.COMMON: 11.0, Rarity.RARE: 15.0, Rarity.EPIC: 19.0, Rarity.MYTHIC: 22.0, Rarity.LEGENDARY: 25.0},
    "heat_reduction": {Rarity.COMMON: 3.5, Rarity.RARE: 5.5, Rarity.EPIC: 7.5, Rarity.MYTHIC: 9.0, Rarity.LEGENDARY: 10.0},
    "drill_cooldown": {Rarity.COMMON: 11, Rarity.RARE: 15, Rarity.EPIC: 19, Rarity.MYTHIC: 23, Rarity.LEGENDARY: 26},
    "scrap_bonus": {Rarity.COMMON: 5.5, Rarity.RARE: 7.5, Rarity.EPIC: 9.0, Rarity.MYTHIC: 10.0, Rarity.LEGENDARY: 12.0},
    "container_chance": {Rarity.COMMON: 3.5, Rarity.RARE: 5.5, Rarity.EPIC: 7.0, Rarity.MYTHIC: 8.0, Rarity.LEGENDARY: 10.0},
}

# Единицы измерения для бафов
BUFF_UNITS = {
    "asteroid_resources": "%",
    "rare_asteroid_chance": "%",
    "double_loot_chance": "%",
    "extra_material_chance": "%",
    "max_energy": "",
    "energy_regen_speed": "%",
    "heat_reduction": "%",
    "drill_cooldown": " сек",
    "scrap_bonus": "%",
    "container_chance": "%",
}


# ===== ДЕБАФЫ (отрицательные эффекты) =====
DEBUFF_KEYS = [
    "resource_reduction",      # Снижение ресурсов (-%)
    "no_resource_chance",      # Шанс не добыть ресурсы (%)
    "rare_asteroid_reduction", # Снижение шанса редкого астероида (-%)
    "max_energy_penalty",      # Макс. энергия (-)
    "energy_regen_penalty",    # Скорость регена энергии (-%)
    "heat_per_click",          # Нагрев за клик (+%)
    "drill_cooldown_penalty",  # Охлаждение бура (+сек)
    "extra_energy_chance",     # Шанс доп. траты энергии (%)
    "double_heat_chance",      # Шанс двойного нагрева (%)
    "scrap_penalty",           # Материалы при разборке (-%)
]

DEBUFF_NAMES = {
    "resource_reduction": "Снижение ресурсов",
    "no_resource_chance": "Шанс не добыть ресурсы",
    "rare_asteroid_reduction": "Снижение шанса редкого астероида",
    "max_energy_penalty": "Максимальная энергия",
    "energy_regen_penalty": "Скорость восстановления энергии",
    "heat_per_click": "Нагрев за клик",
    "drill_cooldown_penalty": "Охлаждение бура",
    "extra_energy_chance": "Шанс потратить дополнительную энергию",
    "double_heat_chance": "Шанс двойного нагрева",
    "scrap_penalty": "Материалы при разборке",
}

# Значения дебафов по редкости (чем выше редкость, тем меньше негатив)
DEBUFF_VALUES = {
    "resource_reduction": {Rarity.COMMON: 11.0, Rarity.RARE: 8.5, Rarity.EPIC: 6.5, Rarity.MYTHIC: 4.5, Rarity.LEGENDARY: 2.5},
    "no_resource_chance": {Rarity.COMMON: 5.5, Rarity.RARE: 4.5, Rarity.EPIC: 3.5, Rarity.MYTHIC: 2.5, Rarity.LEGENDARY: 1.5},
    "rare_asteroid_reduction": {Rarity.COMMON: 9.0, Rarity.RARE: 6.5, Rarity.EPIC: 4.5, Rarity.MYTHIC: 3.5, Rarity.LEGENDARY: 1.5},
    "max_energy_penalty": {Rarity.COMMON: 180, Rarity.RARE: 135, Rarity.EPIC: 100, Rarity.MYTHIC: 70, Rarity.LEGENDARY: 40},
    "energy_regen_penalty": {Rarity.COMMON: 17.5, Rarity.RARE: 13.5, Rarity.EPIC: 9.0, Rarity.MYTHIC: 6.0, Rarity.LEGENDARY: 3.5},
    "heat_per_click": {Rarity.COMMON: 7.0, Rarity.RARE: 5.5, Rarity.EPIC: 3.5, Rarity.MYTHIC: 2.5, Rarity.LEGENDARY: 1.5},
    "drill_cooldown_penalty": {Rarity.COMMON: 13.5, Rarity.RARE: 11.0, Rarity.EPIC: 8.0, Rarity.MYTHIC: 5.5, Rarity.LEGENDARY: 3.5},
    "extra_energy_chance": {Rarity.COMMON: 5.5, Rarity.RARE: 4.5, Rarity.EPIC: 3.5, Rarity.MYTHIC: 2.5, Rarity.LEGENDARY: 1.5},
    "double_heat_chance": {Rarity.COMMON: 3.5, Rarity.RARE: 2.5, Rarity.EPIC: 2.0, Rarity.MYTHIC: 1.5, Rarity.LEGENDARY: 1.0},
    "scrap_penalty": {Rarity.COMMON: 8.5, Rarity.RARE: 6.5, Rarity.EPIC: 4.5, Rarity.MYTHIC: 3.5, Rarity.LEGENDARY: 2.5},
}

DEBUFF_UNITS = {
    "resource_reduction": "%",
    "no_resource_chance": "%",
    "rare_asteroid_reduction": "%",
    "max_energy_penalty": "",
    "energy_regen_penalty": "%",
    "heat_per_click": "%",
    "drill_cooldown_penalty": " сек",
    "extra_energy_chance": "%",
    "double_heat_chance": "%",
    "scrap_penalty": "%",
}


# ===== КОЛИЧЕСТВО ЭФФЕКТОВ ПО РЕДКОСТИ =====
BUFF_COUNT = {
    Rarity.COMMON: (1, 2, 0.7),    # мин, макс, шанс меньшего
    Rarity.RARE: (2, 2, 0.0),      # всегда 2
    Rarity.EPIC: (2, 3, 0.6),      # чаще 2
    Rarity.MYTHIC: (3, 4, 0.7),    # чаще 3
    Rarity.LEGENDARY: (4, 4, 0.0), # всегда 4
}

DEBUFF_COUNT = {
    Rarity.COMMON: (2, 3, 0.3),    # чаще 3
    Rarity.RARE: (1, 2, 0.6),      # чаще 2
    Rarity.EPIC: (1, 2, 0.5),      # равные шансы
    Rarity.MYTHIC: (0, 1, 0.7),    # чаще 1
    Rarity.LEGENDARY: (0, 1, 0.5), # равные шансы
}


# ===== СТОИМОСТЬ УЛУЧШЕНИЯ =====
UPGRADE_COSTS = {
    # С обычной до редкой
    (Rarity.COMMON, Rarity.RARE): {
        "asteroid_rock": 100,
        "cosmic_silicon": 50,
        "metal_fragments": 30,
        "energy_condenser": 10,
        "quantum_fragment": 5,
        "xenotissue": 1,
    },
    # С редкой до эпической
    (Rarity.RARE, Rarity.EPIC): {
        "asteroid_rock": 200,
        "cosmic_silicon": 100,
        "metal_fragments": 60,
        "energy_condenser": 20,
        "quantum_fragment": 10,
        "xenotissue": 3,
        "plasma_core": 1,
    },
    # С эпической до мифической
    (Rarity.EPIC, Rarity.MYTHIC): {
        "asteroid_rock": 400,
        "cosmic_silicon": 200,
        "metal_fragments": 120,
        "energy_condenser": 40,
        "quantum_fragment": 20,
        "xenotissue": 5,
        "plasma_core": 2,
        "astral_crystal": 1,
    },
    # С мифической до легендарной
    (Rarity.MYTHIC, Rarity.LEGENDARY): {
        "asteroid_rock": 800,
        "cosmic_silicon": 400,
        "metal_fragments": 240,
        "energy_condenser": 80,
        "quantum_fragment": 40,
        "xenotissue": 10,
        "plasma_core": 4,
        "astral_crystal": 2,
        "gravity_node": 1,
    },
}


# ===== НАГРАДЫ ЗА РАЗБОРКУ =====
SCRAP_REWARDS = {
    Rarity.COMMON: {
        "asteroid_rock": 15,
        "cosmic_silicon": 8,
        "metal_fragments": 8,
        "energy_condenser": 2,
        "chance": {"quantum_fragment": (30, 1)},
    },
    Rarity.RARE: {
        "asteroid_rock": 40,
        "cosmic_silicon": 20,
        "metal_fragments": 13,
        "energy_condenser": 4,
        "quantum_fragment": 2,
        "chance": {"xenotissue": (40, 1)},
    },
    Rarity.EPIC: {
        "asteroid_rock": 120,
        "cosmic_silicon": 60,
        "metal_fragments": 36,
        "energy_condenser": 13,
        "quantum_fragment": 7,
        "xenotissue": 1,
        "chance": {"xenotissue": (60, 1), "plasma_core": (40, 1)},
    },
    Rarity.MYTHIC: {
        "asteroid_rock": 280,
        "cosmic_silicon": 140,
        "metal_fragments": 85,
        "energy_condenser": 30,
        "quantum_fragment": 14,
        "xenotissue": 3,
        "plasma_core": 1,
        "chance": {"xenotissue": (60, 1), "plasma_core": (40, 1), "astral_crystal": (40, 1)},
    },
    Rarity.LEGENDARY: {
        "asteroid_rock": 600,
        "cosmic_silicon": 300,
        "metal_fragments": 180,
        "energy_condenser": 60,
        "quantum_fragment": 30,
        "xenotissue": 7,
        "plasma_core": 2,
        "astral_crystal": 1,
        "chance": {"xenotissue": (60, 1), "plasma_core": (40, 1), "astral_crystal": (40, 1), "gravity_node": (40, 1)},
    },
}

# Цена продажи (металл)
SELL_PRICE = {
    Rarity.COMMON: 500,
    Rarity.RARE: 1000,
    Rarity.EPIC: 2500,
    Rarity.MYTHIC: 6000,
    Rarity.LEGENDARY: 15000,
}


class ModuleSystem:
    """Система генерации и управления модулями"""

    @staticmethod
    def roll_rarity() -> Rarity:
        """Определить редкость модуля"""
        roll = random.random()
        cumulative = 0.0
        
        for rarity, chance in RARITY_CHANCES.items():
            cumulative += chance
            if roll <= cumulative:
                return rarity
        
        return Rarity.COMMON

    @staticmethod
    def generate_name() -> str:
        """Сгенерировать название модуля: [буквы]-[число]"""
        letters = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', k=2))
        number = random.randint(1, 99)
        return f"{letters}-{number}"

    @staticmethod
    def select_effects(keys: List[str], count_range: Tuple[int, int, float]) -> List[str]:
        """
        Выбрать эффекты из списка.
        
        Args:
            keys: Список ключей эффектов
            count_range: (мин, макс, шанс меньшего)
        
        Returns:
            Список выбранных ключей
        """
        min_count, max_count, chance_lower = count_range
        
        if min_count == max_count:
            count = min_count
        else:
            count = min_count if random.random() < chance_lower else max_count
        
        count = min(count, len(keys))
        return random.sample(keys, count)

    @staticmethod
    def generate_module() -> Dict:
        """
        Сгенерировать новый модуль.
        
        Returns:
            Dict с ключами: name, rarity, buffs, debuffs
        """
        rarity = ModuleSystem.roll_rarity()
        name = ModuleSystem.generate_name()
        
        # Выбираем бафы
        buff_keys = ModuleSystem.select_effects(BUFF_KEYS, BUFF_COUNT[rarity])
        buffs = {key: BUFF_VALUES[key][rarity] for key in buff_keys}
        
        # Выбираем дебафы
        debuff_keys = ModuleSystem.select_effects(DEBUFF_KEYS, DEBUFF_COUNT[rarity])
        debuffs = {key: DEBUFF_VALUES[key][rarity] for key in debuff_keys}
        
        return {
            "name": name,
            "rarity": rarity,
            "buffs": buffs,
            "debuffs": debuffs,
        }

    @staticmethod
    def upgrade_module(buffs: Dict, debuffs: Dict, current_rarity: Rarity) -> Optional[Dict]:
        """
        Улучшить модуль до следующей редкости.
        
        Args:
            buffs: Текущие бафы
            debuffs: Текущие дебафы
            current_rarity: Текущая редкость
        
        Returns:
            Dict с новыми значениями или None если нельзя улучшить
        """
        if current_rarity >= Rarity.LEGENDARY:
            return None
        
        new_rarity = Rarity(current_rarity + 1)
        
        # Обновляем значения бафов
        new_buffs = {}
        for key in buffs.keys():
            new_buffs[key] = BUFF_VALUES[key][new_rarity]
        
        # Обновляем значения дебафов
        new_debuffs = {}
        for key in debuffs.keys():
            new_debuffs[key] = DEBUFF_VALUES[key][new_rarity]
        
        return {
            "rarity": new_rarity,
            "buffs": new_buffs,
            "debuffs": new_debuffs,
        }

    @staticmethod
    def get_upgrade_cost(current_rarity: Rarity) -> Optional[Dict[str, int]]:
        """Получить стоимость улучшения"""
        if current_rarity >= Rarity.LEGENDARY:
            return None
        
        next_rarity = Rarity(current_rarity + 1)
        return UPGRADE_COSTS.get((current_rarity, next_rarity))

    @staticmethod
    def get_scrap_rewards(rarity: Rarity) -> Dict:
        """Получить награды за разборку модуля"""
        return SCRAP_REWARDS.get(rarity, SCRAP_REWARDS[Rarity.COMMON])

    @staticmethod
    def get_sell_price(rarity: Rarity) -> int:
        """Получить цену продажи"""
        return SELL_PRICE.get(rarity, 500)

    @staticmethod
    def format_buff(key: str, value: float) -> str:
        """Форматировать баф для отображения"""
        name = BUFF_NAMES.get(key, key)
        unit = BUFF_UNITS.get(key, "")
        
        if key in ["max_energy"]:
            return f"{name}: +{int(value)}"
        else:
            return f"{name}: +{value}%"

    @staticmethod
    def format_debuff(key: str, value: float) -> str:
        """Форматировать дебаф для отображения"""
        name = DEBUFF_NAMES.get(key, key)
        unit = DEBUFF_UNITS.get(key, "")
        
        if key in ["max_energy_penalty", "drill_cooldown_penalty"]:
            return f"{name}: -{int(value)}{unit}"
        else:
            return f"{name}: +{value}%"

    @staticmethod
    def format_module_card(module: Dict, show_slot: bool = True) -> str:
        """
        Форматировать карточку модуля.
        
        Args:
            module: Dict с ключами module_id, name, rarity, buffs, debuffs, slot
            show_slot: Показывать ли слот
        
        Returns:
            Текст карточки
        """
        name = module.get("name", "??-??")
        module_id = module.get("module_id", "?")
        rarity = Rarity(module.get("rarity", 1))
        buffs = module.get("buffs", {})
        debuffs = module.get("debuffs", {})
        slot = module.get("slot")
        
        text = f"{name} #{module_id}\n\n"
        text += f"Редкость: {RARITY_EMOJI[rarity]} {RARITY_NAME[rarity]}\n"
        
        if show_slot and slot is not None:
            text += f"Надет в слот: {slot}\n"
        
        text += "\n💚 Бафы:\n"
        if buffs:
            for key, value in buffs.items():
                text += f"• {ModuleSystem.format_buff(key, value)}\n"
        else:
            text += "• Нет\n"
        
        text += "\n❤️ Дебафы:\n"
        if debuffs:
            for key, value in debuffs.items():
                text += f"• {ModuleSystem.format_debuff(key, value)}\n"
        else:
            text += "• Нет\n"
        
        return text


# Глобальный экземпляр
module_system = ModuleSystem()
