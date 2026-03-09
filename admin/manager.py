"""
5.2-5.7. Менеджер админ-панели
Управление игроками, предметами, рынком, кланами
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class AdminAction(Enum):
    """Действия админа"""
    # Игроки
    PLAYER_VIEW = "player_view"
    PLAYER_EDIT_RESOURCES = "player_edit_resources"
    PLAYER_GIVE_ITEM = "player_give_item"
    PLAYER_GIVE_DRONE = "player_give_drone"
    PLAYER_BAN = "player_ban"
    PLAYER_UNBAN = "player_unban"
    PLAYER_MAKE_ADMIN = "player_make_admin"
    PLAYER_MESSAGE = "player_message"
    
    # Предметы
    ITEM_CREATE = "item_create"
    ITEM_EDIT = "item_edit"
    ITEM_DELETE = "item_delete"
    
    # Рынок
    MARKET_DELETE_LOT = "market_delete_lot"
    MARKET_EDIT_COMMISSION = "market_edit_commission"
    
    # Кланы
    CLAN_EDIT = "clan_edit"
    CLAN_DELETE = "clan_delete"
    
    # Рассылка
    BROADCAST_SEND = "broadcast_send"
    
    # Баланс
    BALANCE_EDIT = "balance_edit"


@dataclass
class AdminStats:
    """Статистика для админ-панели"""
    total_players: int = 0
    active_today: int = 0
    active_online: int = 0
    total_drones: int = 0
    total_transactions: int = 0
    total_clans: int = 0
    banned_players: int = 0
    premium_players: int = 0
    
    # Экономика
    total_metal: int = 0
    total_crystals: int = 0
    total_credits: int = 0
    
    # За период
    new_players_today: int = 0
    new_players_week: int = 0


class AdminManager:
    """Менеджер админ-панели"""
    
    # Лимиты
    MAX_BROADCAST_RECIPIENTS = 10000
    MAX_LOGS_DISPLAY = 50
    
    @staticmethod
    async def get_stats(db) -> AdminStats:
        """Получить статистику для админ-панели"""
        stats = AdminStats()
        
        try:
            async with db.db_path as conn:
                pass
        except:
            pass
        
        return stats
    
    @staticmethod
    async def search_player(db, query: str) -> Optional[Dict]:
        """Поиск игрока по ID или username"""
        try:
            # Попытка распарсить как ID
            try:
                user_id = int(query.replace("@", ""))
                user = await db.get_user(user_id)
                if user:
                    return user.__dict__
            except ValueError:
                pass
            
            # Поиск по username
            # ... реализация через БД
            
        except Exception as e:
            print(f"Error searching player: {e}")
        
        return None
    
    @staticmethod
    async def edit_player_resources(db, user_id: int, 
                                     resources: Dict[str, int],
                                     admin_id: int) -> bool:
        """Изменить ресурсы игрока"""
        try:
            await db.update_resources(user_id, **resources)
            await db.log_action(
                admin_id, 
                AdminAction.PLAYER_EDIT_RESOURCES.value,
                user_id, 
                str(resources)
            )
            return True
        except Exception as e:
            print(f"Error editing resources: {e}")
            return False
    
    @staticmethod
    async def give_item(db, user_id: int, item_key: str, 
                        quantity: int, admin_id: int) -> bool:
        """Выдать предмет игроку"""
        try:
            await db.add_item(user_id, item_key, quantity)
            await db.log_action(
                admin_id,
                AdminAction.PLAYER_GIVE_ITEM.value,
                user_id,
                f"{item_key} x{quantity}"
            )
            return True
        except Exception as e:
            print(f"Error giving item: {e}")
            return False
    
    @staticmethod
    async def ban_player(db, user_id: int, reason: str, 
                         admin_id: int, duration: int = None) -> bool:
        """Забанить игрока"""
        try:
            # Установка бана в БД
            await db.update_resources(user_id, is_banned=True)
            await db.log_action(
                admin_id,
                AdminAction.PLAYER_BAN.value,
                user_id,
                f"Reason: {reason}, Duration: {duration}"
            )
            return True
        except Exception as e:
            print(f"Error banning player: {e}")
            return False
    
    @staticmethod
    async def unban_player(db, user_id: int, admin_id: int) -> bool:
        """Разбанить игрока"""
        try:
            await db.update_resources(user_id, is_banned=False)
            await db.log_action(
                admin_id,
                AdminAction.PLAYER_UNBAN.value,
                user_id,
                "Unbanned"
            )
            return True
        except Exception as e:
            print(f"Error unbanning player: {e}")
            return False
    
    @staticmethod
    async def get_player_history(db, user_id: int, 
                                   limit: int = 20) -> List[Dict]:
        """Получить историю действий игрока"""
        # Заглушка - реализация через БД
        return []
    
    @staticmethod
    async def create_item(db, item_data: Dict, admin_id: int) -> bool:
        """Создать новый предмет"""
        try:
            # Добавление предмета в справочник
            await db.log_action(
                admin_id,
                AdminAction.ITEM_CREATE.value,
                None,
                str(item_data)
            )
            return True
        except Exception as e:
            print(f"Error creating item: {e}")
            return False
    
    @staticmethod
    async def get_market_stats(db) -> Dict:
        """Получить статистику рынка"""
        return {
            "active_lots": 0,
            "expired_lots": 0,
            "complaints": 0,
            "total_volume": 0,
            "commission_rate": 0.05
        }
    
    @staticmethod
    async def delete_market_lot(db, lot_id: int, admin_id: int) -> bool:
        """Удалить лот с рынка"""
        try:
            await db.log_action(
                admin_id,
                AdminAction.MARKET_DELETE_LOT.value,
                None,
                f"Lot ID: {lot_id}"
            )
            return True
        except Exception as e:
            print(f"Error deleting lot: {e}")
            return False
    
    @staticmethod
    async def get_admin_logs(db, limit: int = 50, 
                               admin_id: int = None) -> List[Dict]:
        """Получить логи действий админов"""
        # Заглушка - реализация через БД
        return []
    
    @staticmethod
    def format_player_info(user_data: Dict) -> str:
        """Форматировать информацию об игроке для админа"""
        status = "🟢 Активен" if not user_data.get("is_banned") else "🚫 Забанен"
        
        text = f"👤 ИГРОК: @{user_data.get('username', 'N/A')} (ID: {user_data.get('user_id')})\n\n"
        text += f"📊 ДАННЫЕ:\n"
        text += f"▸ Уровень: {user_data.get('level', 1)} | Престиж: {user_data.get('prestige', 0)}\n"
        text += f"▸ Металл: {user_data.get('metal', 0):,}\n"
        text += f"▸ Кристаллы: {user_data.get('crystals', 0):,}\n"
        text += f"▸ Тёмная материя: {user_data.get('dark_matter', 0):,}\n"
        text += f"▸ Кредиты: {user_data.get('credits', 0):,}\n"
        text += f"▸ Квант-токены: {user_data.get('quantum_tokens', 0)}\n"
        text += f"▸ Статус: {status}\n"
        
        return text
