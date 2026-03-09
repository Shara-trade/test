"""
Section4: Database - Python Models
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class User:
    """Table4.1 - Users"""
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    level: int = 1
    experience: int = 0
    prestige: int = 0
    tech_tokens: int = 0
    metal: int = 0
    crystals: int = 0
    dark_matter: int = 0
    energy: int = 1000
    max_energy: int = 1000
    credits: int = 0
    quantum_tokens: int = 0
    current_system: str = "alpha_7"
    heat: int = 0
    total_clicks: int = 0
    total_mined: int = 0
    created_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    referral_code: Optional[str] = None
    referred_by: Optional[int] = None
    is_banned: bool = False

    @property
    def is_active(self) -> bool:
        return not self.is_banned


@dataclass
class Drone:
    """Table4.2 - Drones"""
    drone_id: int
    user_id: int
    drone_type: str
    level: int = 1
    income_per_tick: int = 0
    module_slots: int = 1
    installed_modules: str = "[]"
    is_active: bool = True
    acquired_at: Optional[datetime] = None

    DRONE_TYPES = {
        "basic": {"name": "Basic Drone", "slots": 1},
        "miner": {"name": "Miner", "slots": 2},
        "laser": {"name": "Laser", "slots": 3},
        "quantum": {"name": "Quantum", "slots": 4},
        "ai": {"name": "AI Drone", "slots": 5}
    }

    @property
    def name(self) -> str:
        return self.DRONE_TYPES.get(self.drone_type, {}).get("name", "Unknown")


@dataclass
class InventoryItem:
    """Table4.3 - Inventory"""
    item_id: int
    user_id: int
    item_key: str
    quantity: int = 1
    acquired_at: Optional[datetime] = None


@dataclass
class Item:
    """Table4.4 - Items Catalog"""
    item_key: str
    name: str
    description: str
    item_type: str
    rarity: str
    icon: Optional[str] = None
    max_stack: int = 1
    effects: str = "{}"
    level_required: int = 1
    can_sell: bool = True
    base_price: int = 0

    RARITY_EMOJI = {
        "common": "🔹",
        "rare": "🔸",
        "epic": "💜",
        "legendary": "💛",
        "relic": "⚜️"
    }

    @property
    def rarity_emoji(self) -> str:
        return self.RARITY_EMOJI.get(self.rarity, "⚪")


@dataclass
class MarketLot:
    """Table4.5 - Market"""
    lot_id: int
    seller_id: int
    item_key: str
    quantity: int = 1
    price: int = 0
    status: str = "active"
    created_at: Optional[datetime] = None
    sold_at: Optional[datetime] = None

    @property
    def is_active(self) -> bool:
        return self.status == "active"


@dataclass
class Clan:
    """Table4.6 - Clans"""
    clan_id: int
    name: str
    tag: Optional[str] = None
    description: Optional[str] = None
    level: int = 1
    experience: int = 0
    leader_id: Optional[int] = None
    total_mining: int = 0
    members_count: int = 0
    max_members: int = 20
    active_buffs: str = "{}"
    created_at: Optional[datetime] = None


@dataclass
class ClanMember:
    """Table4.7 - Clan Members"""
    member_id: int
    clan_id: int
    user_id: int
    role: str = "member"
    contribution: int = 0
    joined_at: Optional[datetime] = None

    ROLES = {
        "member": "Member",
        "officer": "Officer",
        "leader": "Leader"
    }

    @property
    def role_name(self) -> str:
        return self.ROLES.get(self.role, self.role)


@dataclass
class ClanBoss:
    """Table4.8 - Clan Bosses"""
    boss_id: int
    clan_id: int
    boss_key: str
    level: int = 1
    hp: int = 0
    max_hp: int = 0
    status: str = "active"
    spawned_at: Optional[datetime] = None
    defeated_at: Optional[datetime] = None


@dataclass
class DailyTask:
    """Table4.9 - Daily Tasks"""
    task_id: int
    task_key: str
    name: str
    description: str
    task_type: str
    target_value: int
    reward_metal: int = 0
    reward_crystals: int = 0
    reward_credits: int = 0
    reward_item_key: Optional[str] = None
    difficulty: str = "easy"
    level_required: int = 1


@dataclass
class UserTask:
    """Table4.10 - User Tasks"""
    id: int
    user_id: int
    task_id: int
    progress: int = 0
    completed: bool = False
    completed_at: Optional[datetime] = None
    assigned_date: Optional[str] = None


@dataclass
class Container:
    """Table4.11 - Containers"""
    container_id: int
    user_id: int
    container_type: str
    status: str = "locked"
    unlock_time: Optional[datetime] = None
    created_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    reward_data: Optional[str] = None

    CONTAINER_NAMES = {
        "common": "📦 Common",
        "rare": "💎 Rare",
        "epic": "💜 Epic",
        "legendary": "💛 Legendary"
    }

    @property
    def display_name(self) -> str:
        return self.CONTAINER_NAMES.get(self.container_type, "📦 Container")


@dataclass
class Expedition:
    """Table4.12 - Expeditions"""
    expedition_id: int
    user_id: int
    expedition_type: str
    drones_sent: int = 1
    status: str = "active"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    rewards_claimed: bool = False
    reward_data: Optional[str] = None

    EXPEDITION_NAMES = {
        "near_space": "🚀 Near Space",
        "asteroid_belt": "🚀 Asteroid Belt",
        "nebula": "🚀 Nebula"
    }

    @property
    def name(self) -> str:
        return self.EXPEDITION_NAMES.get(self.expedition_type, "Expedition")


@dataclass
class PrestigeUpgrade:
    """Table4.13 - Prestige Upgrades"""
    upgrade_id: int
    user_id: int
    upgrade_key: str
    level: int = 0
    acquired_at: Optional[datetime] = None

    UPGRADE_NAMES = {
        "mining_efficiency": "⚙️ Mining Efficiency",
        "drone_power": "🤖 Drone Power",
        "energy_capacity": "⚡ Energy Capacity",
        "crit_chance": "💥 Crit Chance",
        "loot_quality": "⭐ Loot Quality",
        "exp_bonus": "📈 EXP Bonus"
    }

    @property
    def name(self) -> str:
        return self.UPGRADE_NAMES.get(self.upgrade_key, self.upgrade_key)


@dataclass
class AdminLog:
    """Table4.14 - Admin Logs"""
    log_id: int
    admin_id: int
    action: str
    target_user_id: Optional[int] = None
    details: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class Referral:
    """Table4.15 - Referrals"""
    referral_id: int
    referrer_id: int
    referred_id: int
    status: str = "pending"
    reward_claimed: bool = False
    created_at: Optional[datetime] = None


@dataclass
class UserStats:
    """User Statistics"""
    stat_id: int
    user_id: int
    weekly_mined: int = 0
    monthly_mined: int = 0
    total_items_found: int = 0
    total_crafted: int = 0
    total_sold: int = 0
    bosses_defeated: int = 0
    updated_at: Optional[datetime] = None
