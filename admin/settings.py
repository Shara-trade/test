"""
Система настроек админ-панели
Хранение и управление конфигурацией в БД
"""
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import aiosqlite


@dataclass
class SettingDefinition:
    """Определение настройки"""
    key: str
    default_value: Any
    setting_type: str  # json, int, float, string, bool
    category: str
    description: str = ""


# Дефолтные настройки
DEFAULT_SETTINGS: Dict[str, SettingDefinition] = {}

# ===== ШАНСЫ РЕДКОСТИ МОДУЛЕЙ =====
DEFAULT_SETTINGS["module_rarity_chances"] = SettingDefinition(
    key="module_rarity_chances",
    default_value={
        "common": 70.0,
        "rare": 20.0,
        "epic": 7.0,
        "mythic": 2.5,
        "legendary": 0.5
    },
    setting_type="json",
    category="drop",
    description="Шансы выпадения редкости модулей (в процентах)"
)

# ===== ЦЕНА ПРОДАЖИ МОДУЛЕЙ =====
DEFAULT_SETTINGS["module_sell_prices"] = SettingDefinition(
    key="module_sell_prices",
    default_value={
        "base": 1500,
        "multipliers": {
            "common": 1.0,
            "rare": 2.0,
            "epic": 4.0,
            "mythic": 8.0,
            "legendary": 16.0
        }
    },
    setting_type="json",
    category="economy",
    description="Цены продажи модулей"
)

# ===== ЛИМИТЫ ВЫДАЧИ =====
DEFAULT_SETTINGS["admin_limits"] = SettingDefinition(
    key="admin_limits",
    default_value={
        "max_containers_per_give": 100,
        "max_materials_per_give": 1000,
        "max_gives_per_day": 500,
        "max_bans_per_hour": 20
    },
    setting_type="json",
    category="limits",
    description="Лимиты выдачи для администраторов"
)

# ===== АНТИСПАМ =====
DEFAULT_SETTINGS["antispam_limits"] = SettingDefinition(
    key="antispam_limits",
    default_value={
        "messages_per_minute": 20,
        "container_opens_per_minute": 5,
        "module_upgrades_per_hour": 10,
        "ban_duration_minutes": 5
    },
    setting_type="json",
    category="limits",
    description="Лимиты антиспама для игроков"
)

# ===== ШАНСЫ КОНТЕЙНЕРОВ =====
DEFAULT_SETTINGS["container_drop_chances"] = SettingDefinition(
    key="container_drop_chances",
    default_value={
        "common": 0.65,
        "rare": 0.20,
        "epic": 0.09,
        "mythic": 0.04,
        "legendary": 0.02
    },
    setting_type="json",
    category="containers",
    description="Шансы выпадения типов контейнеров"
)

# ===== НАГРАДЫ КОНТЕЙНЕРОВ =====
DEFAULT_SETTINGS["container_rewards"] = SettingDefinition(
    key="container_rewards",
    default_value={
        "common": {"metal_min": 50, "metal_max": 100, "crystals_min": 10, "crystals_max": 25, "dark_matter_min": 0, "dark_matter_max": 5},
        "rare": {"metal_min": 150, "metal_max": 300, "crystals_min": 40, "crystals_max": 80, "dark_matter_min": 10, "dark_matter_max": 25},
        "epic": {"metal_min": 400, "metal_max": 800, "crystals_min": 120, "crystals_max": 250, "dark_matter_min": 40, "dark_matter_max": 80},
        "mythic": {"metal_min": 900, "metal_max": 1800, "crystals_min": 300, "crystals_max": 600, "dark_matter_min": 120, "dark_matter_max": 250},
        "legendary": {"metal_min": 2000, "metal_max": 5000, "crystals_min": 800, "crystals_max": 2000, "dark_matter_min": 300, "dark_matter_max": 800}
    },
    setting_type="json",
    category="containers",
    description="Награды из контейнеров (диапазоны)"
)

# ===== СТОИМОСТЬ УЛУЧШЕНИЯ МОДУЛЕЙ =====
DEFAULT_SETTINGS["module_upgrade_costs"] = SettingDefinition(
    key="module_upgrade_costs",
    default_value={
        "common_to_rare": {"asteroid_rock": 100, "cosmic_silicon": 50, "metal_fragments": 30, "energy_condenser": 10, "quantum_fragment": 5, "xenotissue": 1},
        "rare_to_epic": {"asteroid_rock": 200, "cosmic_silicon": 100, "metal_fragments": 60, "energy_condenser": 20, "quantum_fragment": 10, "xenotissue": 3, "plasma_core": 1},
        "epic_to_mythic": {"asteroid_rock": 400, "cosmic_silicon": 200, "metal_fragments": 120, "energy_condenser": 40, "quantum_fragment": 20, "xenotissue": 5, "plasma_core": 2, "astral_crystal": 1},
        "mythic_to_legendary": {"asteroid_rock": 800, "cosmic_silicon": 400, "metal_fragments": 240, "energy_condenser": 80, "quantum_fragment": 40, "xenotissue": 10, "plasma_core": 4, "astral_crystal": 2, "gravity_node": 1}
    },
    setting_type="json",
    category="economy",
    description="Стоимость улучшения модулей"
)

# ===== ЗНАЧЕНИЯ БАФОВ ПО РЕДКОСТИ =====
DEFAULT_SETTINGS["buff_values"] = SettingDefinition(
    key="buff_values",
    default_value={
        "asteroid_resources": {"common": 5.5, "rare": 7.5, "epic": 9.5, "mythic": 11.0, "legendary": 12.0},
        "rare_asteroid_chance": {"common": 2.5, "rare": 3.5, "epic": 5.0, "mythic": 6.0, "legendary": 7.0},
        "double_loot_chance": {"common": 3.5, "rare": 4.5, "epic": 6.0, "mythic": 7.0, "legendary": 8.0},
        "extra_material_chance": {"common": 4.5, "rare": 6.5, "epic": 8.0, "mythic": 9.0, "legendary": 10.0},
        "max_energy": {"common": 120, "rare": 180, "epic": 230, "mythic": 270, "legendary": 300},
        "energy_regen_speed": {"common": 11.0, "rare": 15.0, "epic": 19.0, "mythic": 22.0, "legendary": 25.0},
        "heat_reduction": {"common": 3.5, "rare": 5.5, "epic": 7.5, "mythic": 9.0, "legendary": 10.0},
        "drill_cooldown": {"common": 11, "rare": 15, "epic": 19, "mythic": 23, "legendary": 26},
        "scrap_bonus": {"common": 5.5, "rare": 7.5, "epic": 9.0, "mythic": 10.0, "legendary": 12.0},
        "container_chance": {"common": 3.5, "rare": 5.5, "epic": 7.0, "mythic": 8.0, "legendary": 10.0}
    },
    setting_type="json",
    category="modules",
    description="Значения бафов по редкости"
)

# ===== ЗНАЧЕНИЯ ДЕБАФОВ ПО РЕДКОСТИ =====
DEFAULT_SETTINGS["debuff_values"] = SettingDefinition(
    key="debuff_values",
    default_value={
        "resource_reduction": {"common": 11.0, "rare": 8.5, "epic": 6.5, "mythic": 4.5, "legendary": 2.5},
        "no_resource_chance": {"common": 5.5, "rare": 4.5, "epic": 3.5, "mythic": 2.5, "legendary": 1.5},
        "rare_asteroid_reduction": {"common": 9.0, "rare": 6.5, "epic": 4.5, "mythic": 3.5, "legendary": 1.5},
        "max_energy_penalty": {"common": 180, "rare": 135, "epic": 100, "mythic": 70, "legendary": 40},
        "energy_regen_penalty": {"common": 17.5, "rare": 13.5, "epic": 9.0, "mythic": 6.0, "legendary": 3.5},
        "heat_per_click": {"common": 7.0, "rare": 5.5, "epic": 3.5, "mythic": 2.5, "legendary": 1.5},
        "drill_cooldown_penalty": {"common": 13.5, "rare": 11.0, "epic": 8.0, "mythic": 5.5, "legendary": 3.5},
        "extra_energy_chance": {"common": 5.5, "rare": 4.5, "epic": 3.5, "mythic": 2.5, "legendary": 1.5},
        "double_heat_chance": {"common": 3.5, "rare": 2.5, "epic": 2.0, "mythic": 1.5, "legendary": 1.0},
        "scrap_penalty": {"common": 8.5, "rare": 6.5, "epic": 4.5, "mythic": 3.5, "legendary": 2.5}
    },
    setting_type="json",
    category="modules",
    description="Значения дебафов по редкости"
)


class AdminSettingsManager:
    """Менеджер настроек админ-панели"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._cache: Dict[str, Any] = {}
    
    async def init_settings(self):
        """Инициализация настроек (создание дефолтных если нет)"""
        async with aiosqlite.connect(self.db_path) as db:
            for key, definition in DEFAULT_SETTINGS.items():
                # Проверяем существование
                async with db.execute(
                    "SELECT setting_key FROM admin_settings WHERE setting_key = ?",
                    (key,)
                ) as cursor:
                    row = await cursor.fetchone()
                
                if not row:
                    # Создаём с дефолтным значением
                    value_json = json.dumps(definition.default_value, ensure_ascii=False)
                    await db.execute(
                        """INSERT INTO admin_settings (setting_key, setting_value, setting_type, category, description)
                           VALUES (?, ?, ?, ?, ?)""",
                        (key, value_json, definition.setting_type, definition.category, definition.description)
                    )
            
            await db.commit()
    
    async def get(self, key: str, use_cache: bool = True) -> Optional[Any]:
        """Получить настройку"""
        if use_cache and key in self._cache:
            return self._cache[key]
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT setting_value, setting_type FROM admin_settings WHERE setting_key = ?",
                (key,)
            ) as cursor:
                row = await cursor.fetchone()
            
            if not row:
                # Возвращаем дефолтное значение
                if key in DEFAULT_SETTINGS:
                    return DEFAULT_SETTINGS[key].default_value
                return None
            
            value_json, setting_type = row
            
            try:
                value = json.loads(value_json)
            except:
                value = value_json
            
            if use_cache:
                self._cache[key] = value
            
            return value
    
    async def set(self, key: str, value: Any, admin_id: int = None) -> bool:
        """Установить настройку"""
        async with aiosqlite.connect(self.db_path) as db:
            value_json = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
            
            await db.execute(
                """INSERT INTO admin_settings (setting_key, setting_value, updated_at, updated_by)
                   VALUES (?, ?, CURRENT_TIMESTAMP, ?)
                   ON CONFLICT(setting_key) DO UPDATE SET 
                   setting_value = excluded.setting_value,
                   updated_at = CURRENT_TIMESTAMP,
                   updated_by = excluded.updated_by""",
                (key, value_json, admin_id)
            )
            await db.commit()
        
        # Обновляем кэш
        self._cache[key] = value
        return True
    
    async def get_category(self, category: str) -> Dict[str, Any]:
        """Получить все настройки категории"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT setting_key, setting_value FROM admin_settings WHERE category = ?",
                (category,)
            ) as cursor:
                rows = await cursor.fetchall()
            
            result = {}
            for key, value_json in rows:
                try:
                    result[key] = json.loads(value_json)
                except:
                    result[key] = value_json
            
            return result
    
    async def get_all_categories(self) -> List[str]:
        """Получить список всех категорий"""
        return ["drop", "economy", "containers", "modules", "materials", "limits"]
    
    def invalidate_cache(self, key: str = None):
        """Сбросить кэш"""
        if key:
            self._cache.pop(key, None)
        else:
            self._cache.clear()
    
    # Удобные методы для конкретных настроек
    
    async def get_rarity_chances(self) -> Dict[str, float]:
        """Получить шансы редкости модулей"""
        return await self.get("module_rarity_chances")
    
    async def set_rarity_chances(self, chances: Dict[str, float], admin_id: int = None) -> bool:
        """Установить шансы редкости"""
        return await self.set("module_rarity_chances", chances, admin_id)
    
    async def get_sell_prices(self) -> Dict:
        """Получить цены продажи модулей"""
        return await self.get("module_sell_prices")
    
    async def get_admin_limits(self) -> Dict:
        """Получить лимиты выдачи"""
        return await self.get("admin_limits")
    
    async def get_antispam_limits(self) -> Dict:
        """Получить лимиты антиспама"""
        return await self.get("antispam_limits")
    
    async def get_container_rewards(self) -> Dict:
        """Получить награды контейнеров"""
        return await self.get("container_rewards")
    
    async def get_buff_values(self) -> Dict:
        """Получить значения бафов"""
        return await self.get("buff_values")
    
    async def get_debuff_values(self) -> Dict:
        """Получить значения дебафов"""
        return await self.get("debuff_values")
    
    async def get_upgrade_costs(self) -> Dict:
        """Получить стоимость улучшения"""
        return await self.get("module_upgrade_costs")


# Пресеты шансов редкости
RARITY_PRESETS = {
    "standard": {"common": 70.0, "rare": 20.0, "epic": 7.0, "mythic": 2.5, "legendary": 0.5},
    "fast": {"common": 50.0, "rare": 30.0, "epic": 15.0, "mythic": 4.0, "legendary": 1.0},
    "generous": {"common": 40.0, "rare": 30.0, "epic": 20.0, "mythic": 8.0, "legendary": 2.0},
    "hardcore": {"common": 85.0, "rare": 10.0, "epic": 4.0, "mythic": 0.9, "legendary": 0.1},
}
