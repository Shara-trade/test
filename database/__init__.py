"""
Section4: Database Structure
"""
from .models import (
    User, Drone, InventoryItem, Item, MarketLot,
    Clan, ClanMember, ClanBoss, DailyTask, UserTask,
    Container, Expedition, PrestigeUpgrade, AdminLog,
    Referral, UserStats
)
from .db_manager import DatabaseManager, db_manager

# Alias for backward compatibility
db = db_manager

__all__ = [
    "User", "Drone", "InventoryItem", "Item", "MarketLot",
    "Clan", "ClanMember", "ClanBoss", "DailyTask", "UserTask",
    "Container", "Expedition", "PrestigeUpgrade", "AdminLog",
    "Referral", "UserStats",
    "DatabaseManager", "db_manager", "db"
]
