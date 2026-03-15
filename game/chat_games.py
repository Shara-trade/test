"""
3.14. Система чат-игр
Групповые ивенты в чатах
"""
import random
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum


class ChatEventType(Enum):
    ASTEROID = "asteroid"
    BOSS = "boss"
    TREASURE = "treasure"
    RAID = "raid"


@dataclass
class ChatEvent:
    """Событие в чате"""
    event_id: int
    chat_id: int
    event_type: ChatEventType
    hp_max: int
    hp_current: int
    damage_per_click: tuple  # (min, max)
    started_at: datetime
    ends_at: datetime
    participants: Dict[int, int] = None  # user_id: damage_dealt
    is_active: bool = True
    
    def __post_init__(self):
        if self.participants is None:
            self.participants = {}
    
    @property
    def time_remaining(self) -> int:
        """Секунд до конца события"""
        delta = self.ends_at - datetime.now()
        return max(0, int(delta.total_seconds()))
    
    @property
    def is_defeated(self) -> bool:
        """Побежден ли босс/астероид"""
        return self.hp_current <= 0
    
    @property
    def total_damage(self) -> int:
        """Общий нанесенный урон"""
        return sum(self.participants.values()) if self.participants else 0


class ChatGamesSystem:
    """Система чат-игр"""
    
    # Интервалы автоматических событий
    AUTO_EVENT_INTERVAL_HOURS = 3
    EVENT_DURATION_MINUTES = 10
    
    # Параметры событий
    EVENT_CONFIGS = {
        ChatEventType.ASTEROID: {
            "name": "Астероид",
            "emoji": "☄️",
            "hp_base": 5000,
            "hp_per_member": 100,
            "damage_range": (10, 20),
            "xp_reward": 50
        },
        ChatEventType.BOSS: {
            "name": "Космический босс",
            "emoji": "👾",
            "hp_base": 10000,
            "hp_per_member": 200,
            "damage_range": (15, 30),
            "xp_reward": 100
        },
        ChatEventType.TREASURE: {
            "name": "Сундук",
            "emoji": "📦",
            "hp_base": 3000,
            "hp_per_member": 50,
            "damage_range": (5, 15),
            "xp_reward": 30
        },
        ChatEventType.RAID: {
            "name": "Рейд пиратов",
            "emoji": "🚀",
            "hp_base": 15000,
            "hp_per_member": 300,
            "damage_range": (20, 40),
            "xp_reward": 150
        }
    }
    
    @staticmethod
    def create_event(chat_id: int, event_type: ChatEventType, 
                     member_count: int = 1) -> ChatEvent:
        """Создать событие в чате"""
        config = ChatGamesSystem.EVENT_CONFIGS[event_type]
        
        hp_max = config["hp_base"] + (config["hp_per_member"] * min(member_count, 50))
        damage_range = config["damage_range"]
        
        now = datetime.now()
        ends_at = now + timedelta(minutes=ChatGamesSystem.EVENT_DURATION_MINUTES)
        
        return ChatEvent(
            event_id=random.randint(100000, 999999),
            chat_id=chat_id,
            event_type=event_type,
            hp_max=hp_max,
            hp_current=hp_max,
            damage_per_click=damage_range,
            started_at=now,
            ends_at=ends_at
        )
    
    @staticmethod
    def process_click(event: ChatEvent, user_id: int) -> Dict:
        """Обработать клик по событию"""
        if not event.is_active or event.is_defeated:
            return {"success": False, "reason": "event_ended"}
        
        if event.time_remaining <= 0:
            event.is_active = False
            return {"success": False, "reason": "time_up"}
        
        # Расчет урона
        min_dmg, max_dmg = event.damage_per_click
        damage = random.randint(min_dmg, max_dmg)
        
        # Крит (10% шанс)
        is_crit = random.random() < 0.1
        if is_crit:
            damage *= 2
        
        # Применение урона
        event.hp_current = max(0, event.hp_current - damage)
        
        # Запись участника
        if user_id not in event.participants:
            event.participants[user_id] = 0
        event.participants[user_id] += damage
        
        result = {
            "success": True,
            "damage": damage,
            "is_crit": is_crit,
            "hp_remaining": event.hp_current,
            "hp_max": event.hp_max,
            "is_defeated": event.is_defeated
        }
        
        # Если побежден
        if event.is_defeated:
            event.is_active = False
            result["rewards"] = ChatGamesSystem.calculate_rewards(event)
        
        return result
    
    @staticmethod
    def calculate_rewards(event: ChatEvent) -> Dict[int, Dict]:
        """Рассчитать награды для участников"""
        rewards = {}
        config = ChatGamesSystem.EVENT_CONFIGS[event.event_type]
        
        # Сортировка по урону
        sorted_participants = sorted(
            event.participants.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        total_participants = len(sorted_participants)
        
        for rank, (user_id, damage) in enumerate(sorted_participants, 1):
            # Базовая награда
            base_metal = 100 + (damage // 10)
            base_crystals = 10 + (damage // 100)
            
            # Бонус за топ-3
            rank_bonus = {1: 3.0, 2: 2.0, 3: 1.5}.get(rank, 1.0)
            
            # Шанс на предмет
            item_chance = 0.05 + (rank * 0.02)
            item_key = None
            if random.random() < item_chance:
                item_key = random.choice([
                    "laser_mk1", "battery_mk1", "scanner_mk1"
                ])
            
            rewards[user_id] = {
                "rank": rank,
                "damage_dealt": damage,
                "damage_percent": int((damage / event.hp_max) * 100),
                "metal": int(base_metal * rank_bonus),
                "crystals": int(base_crystals * rank_bonus),
                "xp": config["xp_reward"],
                "item_key": item_key
            }
        
        return rewards
    
    @staticmethod
    def get_event_message(event: ChatEvent) -> str:
        """Получить текст события для отображения"""
        config = ChatGamesSystem.EVENT_CONFIGS[event.event_type]
        
        hp_percent = (event.hp_current / event.hp_max) * 100
        hp_bar = ChatGamesSystem._generate_hp_bar(hp_percent)
        
        message = f"{config['emoji']} В ЧАТ ПРИЛЕТЕЛ {config['name'].upper()}!\n"
        message += f"Все вместе атакуйте!\n\n"
        message += f"❤️ HP: {event.hp_current:,}/{event.hp_max:,}\n"
        message += f"{hp_bar} {int(hp_percent)}%\n\n"
        message += f"⚔️ Урон за клик: {event.damage_per_click[0]}-{event.damage_per_click[1]}\n"
        message += f"👥 Участников: {len(event.participants)}\n"
        message += f"⏱ Осталось: {event.time_remaining // 60} мин {event.time_remaining % 60} сек"
        
        return message
    
    @staticmethod
    def _generate_hp_bar(percent: float) -> str:
        """Генерировать полоску HP"""
        filled = int(percent / 5)
        empty = 20 - filled
        
        if percent > 50:
            return "🟩" * filled + "⬜" * empty
        elif percent > 25:
            return "🟨" * filled + "⬜" * empty
        else:
            return "🟥" * filled + "⬜" * empty


@dataclass
class ChatStats:
    """Статистика чата"""
    chat_id: int
    total_events: int = 0
    events_won: int = 0
    total_damage: int = 0
    last_event: Optional[datetime] = None
    
    @property
    def win_rate(self) -> float:
        if self.total_events == 0:
            return 0.0
        return (self.events_won / self.total_events) * 100
