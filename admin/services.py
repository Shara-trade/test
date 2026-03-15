"""
Сервисы бизнес-логики для админ-панели
Отвечают за обработку данных, кэширование и валидацию
"""
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import json

from .repositories import AdminRepository
from .schemas import (
    ResourceUpdateSchema, ResourceSingleUpdateSchema,
    GiveContainerSchema, GiveMaterialSchema, GiveModuleSchema,
    BanPlayerSchema, PlayerSearchSchema, BanDuration
)


class AdminCacheService:
    """
    Сервис кэширования для админ-панели.
    
    Кэширует:
    - Карточки игроков (60 сек)
    - Статистику (300 сек)
    - Логи (60 сек)
    """
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._ttl: Dict[str, int] = {
            "player_card": 60,
            "stats": 300,
            "logs": 60,
            "admin_role": 300,
            "settings": 600
        }
        self._expiry: Dict[str, datetime] = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша"""
        if key not in self._cache:
            return None
        
        # Проверяем TTL
        if key in self._expiry and datetime.now() > self._expiry[key]:
            del self._cache[key]
            del self._expiry[key]
            return None
        
        return self._cache[key]
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Установить значение в кэш"""
        self._cache[key] = value
        
        # Определяем TTL
        for prefix, default_ttl in self._ttl.items():
            if key.startswith(prefix):
                ttl = ttl or default_ttl
                break
        
        ttl = ttl or 60  # По умолчанию 60 сек
        self._expiry[key] = datetime.now() + timedelta(seconds=ttl)
    
    async def delete(self, key: str):
        """Удалить значение из кэша"""
        self._cache.pop(key, None)
        self._expiry.pop(key, None)
    
    async def invalidate_player(self, user_id: int):
        """Инвалидировать кэш игрока"""
        await self.delete(f"player_card:{user_id}")
        await self.delete(f"admin_role:{user_id}")
    
    async def clear_all(self):
        """Очистить весь кэш"""
        self._cache.clear()
        self._expiry.clear()


class AdminService:
    """
    Основной сервис админ-панели.
    
    Отвечает за:
    - Управление игроками
    - Выдачу предметов
    - Статистику
    - Логирование
    """
    
    # Права по ролям
    ROLE_PERMISSIONS = {
        "owner": ["all"],
        "senior": ["players", "containers", "modules", "drop", "economy", "materials", "stats", "logs", "testing", "events", "backups", "metrics"],
        "moderator": ["players", "containers", "modules", "materials", "stats", "logs"],
        "support": ["stats", "logs"]
    }
    
    # Роль по умолчанию
    DEFAULT_ROLE = "support"
    
    def __init__(self, repository: AdminRepository):
        self.repo = repository
        self.cache = AdminCacheService()
    
    # ==================== ИГРОКИ ====================
    
    async def get_player(self, user_id: int, use_cache: bool = True) -> Optional[Dict]:
        """
        Получить данные игрока.
        
        Args:
            user_id: ID пользователя
            use_cache: Использовать кэш
            
        Returns:
            Dict с данными игрока
        """
        if use_cache:
            cached = await self.cache.get(f"player_card:{user_id}")
            if cached:
                return cached
        
        player = await self.repo.get_player_card_data(user_id)
        
        if player and use_cache:
            await self.cache.set(f"player_card:{user_id}", player)
        
        return player
    
    async def search_players(self, query: str) -> Dict:
        """
        Поиск игроков с валидацией.
        
        Args:
            query: Поисковый запрос
            
        Returns:
            Dict с результатами поиска
        """
        # Валидация
        try:
            schema = PlayerSearchSchema(query=query)
        except Exception as e:
            return {"success": False, "error": str(e)}
        
        players = await self.repo.search_players(schema.query)
        
        return {
            "success": True,
            "players": players,
            "count": len(players)
        }
    
    async def search_players_advanced(
        self,
        query: Optional[str] = None,
        min_level: Optional[int] = None,
        max_level: Optional[int] = None,
        is_banned: Optional[bool] = None,
        is_admin: Optional[bool] = None,
        min_metal: Optional[int] = None,
        min_crystals: Optional[int] = None,
        registered_after: Optional[str] = None,
        registered_before: Optional[str] = None,
        last_activity_after: Optional[str] = None,
        limit: int = 20,
        page: int = 1
    ) -> Dict:
        """
        Расширенный поиск игроков с фильтрами.
        
        Args:
            query: Поисковый запрос
            min_level: Минимальный уровень
            max_level: Максимальный уровень
            is_banned: Только забаненные/незабаненные
            is_admin: Только админы/не админы
            min_metal: Минимум металла
            min_crystals: Минимум кристаллов
            registered_after: Зарегистрирован после
            registered_before: Зарегистрирован до
            last_activity_after: Активен после
            limit: Лимит результатов
            page: Номер страницы
            
        Returns:
            Dict с результатами
        """
        offset = (page - 1) * limit
        
        result = await self.repo.search_players_advanced(
            query=query,
            min_level=min_level,
            max_level=max_level,
            is_banned=is_banned,
            is_admin=is_admin,
            min_metal=min_metal,
            min_crystals=min_crystals,
            registered_after=registered_after,
            registered_before=registered_before,
            last_activity_after=last_activity_after,
            limit=limit,
            offset=offset
        )
        
        return {
            "success": True,
            "players": result["players"],
            "total": result["total"],
            "page": page,
            "has_more": result["has_more"]
        }
    
    async def update_player_resource(
        self,
        user_id: int,
        resource_type: str,
        new_value: int,
        admin_id: int
    ) -> Dict:
        """
        Обновить один ресурс игрока.
        
        Args:
            user_id: ID пользователя
            resource_type: Тип ресурса (metal, crystals, dark_matter, credits)
            new_value: Новое значение
            admin_id: ID админа
            
        Returns:
            Dict с результатом
        """
        # Валидация
        try:
            schema = ResourceSingleUpdateSchema(
                resource_type=resource_type,
                value=new_value,
                user_id=user_id
            )
        except Exception as e:
            return {"success": False, "error": str(e)}
            
        # Получаем текущее значение
        player = await self.repo.get_player(user_id)
        if not player:
            return {"success": False, "error": "Игрок не найден"}
        
        old_value = player.get(resource_type, 0)
        
        # Обновляем
        success = await self.repo.update_resources(
            user_id=user_id,
            admin_id=admin_id,
            resources={resource_type: new_value},
            log_details=f"{resource_type}: {old_value} -> {new_value}"
        )
        
        if success:
            # Инвалидируем кэш
            await self.cache.invalidate_player(user_id)
        
            return {
                "success": True,
                "old_value": old_value,
                "new_value": new_value,
                "resource_type": resource_type
            }
        
        return {"success": False, "error": "Ошибка обновления"}
    
    async def update_player_resources(
        self,
        user_id: int,
        resources: Dict[str, int],
        admin_id: int
    ) -> Dict:
        """
        Обновить несколько ресурсов игрока.
        
        Args:
            user_id: ID пользователя
            resources: Dict с ресурсами
            admin_id: ID админа
            
        Returns:
            Dict с результатом
        """
        # Валидация
        try:
            schema = ResourceUpdateSchema(**resources)
        except Exception as e:
            return {"success": False, "error": str(e)}
        
        # Получаем текущие значения
        player = await self.repo.get_player(user_id)
        if not player:
            return {"success": False, "error": "Игрок не найден"}
        
        old_values = {k: player.get(k, 0) for k in resources.keys()}
        
        # Обновляем
        success = await self.repo.update_resources(
            user_id=user_id,
            admin_id=admin_id,
            resources=resources
        )
        
        if success:
            await self.cache.invalidate_player(user_id)
            
            return {
                "success": True,
                "old_values": old_values,
                "new_values": resources
            }
        
        return {"success": False, "error": "Ошибка обновления"}
    
    # ==================== ВЫДАЧА ====================
    
    async def give_container(
        self,
        user_id: int,
        container_type: str,
        quantity: int,
        admin_id: int
    ) -> Dict:
        """
        Выдать контейнеры игроку.
        
        Args:
            user_id: ID пользователя
            container_type: Тип контейнера
            quantity: Количество
            admin_id: ID админа
            
        Returns:
            Dict с результатом
        """
        # Валидация
        try:
            schema = GiveContainerSchema(
                user_id=user_id,
                container_type=container_type,
                quantity=quantity
            )
        except Exception as e:
            return {"success": False, "error": str(e)}
        
        # Проверяем существование игрока
        player = await self.repo.get_player(user_id)
        if not player:
            return {"success": False, "error": "Игрок не найден"}
        
        # Выдаём
        item_key = f"container_{container_type}"
        result = await self.repo.give_item(
            user_id=user_id,
            item_key=item_key,
            quantity=quantity,
            admin_id=admin_id
        )
        
        if result.get("success"):
            await self.cache.invalidate_player(user_id)
            
            return {
                "success": True,
                "item_key": item_key,
                "quantity": quantity,
                "user_id": user_id
            }
        
        return result
    
    async def give_material(
        self,
        user_id: int,
        material_key: str,
        quantity: int,
        admin_id: int
    ) -> Dict:
        """
        Выдать материал игроку.
        
        Args:
            user_id: ID пользователя
            material_key: Ключ материала
            quantity: Количество
            admin_id: ID админа
            
        Returns:
            Dict с результатом
        """
        # Валидация
        try:
            schema = GiveMaterialSchema(
                user_id=user_id,
                material_key=material_key,
                quantity=quantity
            )
        except Exception as e:
            return {"success": False, "error": str(e)}
        
        # Проверяем существование игрока
        player = await self.repo.get_player(user_id)
        if not player:
            return {"success": False, "error": "Игрок не найден"}
        
        # Выдаём
        result = await self.repo.give_item(
            user_id=user_id,
            item_key=material_key,
            quantity=quantity,
            admin_id=admin_id
        )
        
        if result.get("success"):
            await self.cache.invalidate_player(user_id)
            
            return {
                "success": True,
                "material_key": material_key,
                "quantity": quantity,
                "user_id": user_id
            }
        
        return result
    
    async def give_module(
        self,
        user_id: int,
        module_data: Dict,
        admin_id: int
    ) -> Dict:
        """
        Выдать модуль игроку.
        
        Args:
            user_id: ID пользователя
            module_data: Данные модуля
            admin_id: ID админа
            
        Returns:
            Dict с результатом
        """
        # Валидация
        try:
            schema = GiveModuleSchema(
                user_id=user_id,
                rarity=module_data.get("rarity", "common"),
                name=module_data.get("name")
            )
        except Exception as e:
            return {"success": False, "error": str(e)}
        
        # Проверяем существование игрока
        player = await self.repo.get_player(user_id)
        if not player:
            return {"success": False, "error": "Игрок не найден"}
        
        # Выдаём
        result = await self.repo.give_module(
            user_id=user_id,
            module_data=module_data,
            admin_id=admin_id
        )
        
        if result.get("success"):
            await self.cache.invalidate_player(user_id)
        
        return result
    
    # ==================== БАН ====================
    
    async def ban_player(
        self,
        user_id: int,
        reason: str,
        admin_id: int,
        duration: Optional[str] = None,
        custom_hours: Optional[int] = None
    ) -> Dict:
        """
        Забанить игрока.
        
        Args:
            user_id: ID пользователя
            reason: Причина
            admin_id: ID админа
            duration: Длительность (1h, 24h, 7d, forever, custom)
            custom_hours: Кастомное время в часах
            
        Returns:
            Dict с результатом
        """
        # Валидация
        try:
            schema = BanPlayerSchema(
                user_id=user_id,
                reason=reason,
                duration=duration,
                custom_hours=custom_hours
            )
        except Exception as e:
            return {"success": False, "error": str(e)}
        
        # Нельзя забанить owner
        target_role = await self.repo.get_admin_role(user_id)
        if target_role == "owner":
            return {"success": False, "error": "Нельзя забанить владельца"}
        
        # Вычисляем длительность в часах
        duration_hours = None
        if duration:
            duration_map = {
                "1h": 1,
                "24h": 24,
                "7d": 168,
                "forever": None,
                "custom": custom_hours
            }
            duration_hours = duration_map.get(duration, custom_hours)
        
        # Баним
        result = await self.repo.ban_player(
            user_id=user_id,
            admin_id=admin_id,
            reason=reason,
            duration_hours=duration_hours
        )
        
        if result.get("success"):
            await self.cache.invalidate_player(user_id)
        
        return result
    
    async def unban_player(self, user_id: int, admin_id: int) -> Dict:
        """
        Разбанить игрока.
        
        Args:
            user_id: ID пользователя
            admin_id: ID админа
            
        Returns:
            Dict с результатом
        """
        # Разбаниваем
        result = await self.repo.unban_player(user_id=user_id, admin_id=admin_id)
        
        if result.get("success"):
            await self.cache.invalidate_player(user_id)
        
        return result
    
    # ==================== ИСТОРИЯ ====================
    
    async def get_player_history(
        self,
        user_id: int,
        limit: int = 20,
        page: int = 1
    ) -> Dict:
        """
        Получить историю действий над игроком.
        
        Args:
            user_id: ID пользователя
            limit: Количество записей
            page: Номер страницы
            
        Returns:
            Dict с историей
        """
        offset = (page - 1) * limit
        
        events = await self.repo.get_player_history(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        return {
            "success": True,
            "user_id": user_id,
            "events": events,
            "page": page,
            "has_more": len(events) == limit
        }
    
    # ==================== СТАТИСТИКА ====================
    
    async def get_stats(self, use_cache: bool = True) -> Dict:
        """
        Получить статистику для админ-панели.
        
        Args:
            use_cache: Использовать кэш
            
        Returns:
            Dict со статистикой
        """
        if use_cache:
            cached = await self.cache.get("stats:main")
            if cached:
                return cached
        
        stats = await self.repo.get_admin_stats()
        
        if use_cache:
            await self.cache.set("stats:main", stats)
        
        return stats
    
    async def get_realtime_stats(self) -> Dict:
        """
        Получить статистику в реальном времени.
        
        Returns:
            Dict с метриками
        """
        return await self.repo.get_realtime_stats()
    
    async def get_activity_stats(self, days: int = 7) -> Dict:
        """
        Получить статистику активности по дням.
        
        Args:
            days: Количество дней
            
        Returns:
            Dict со статистикой
        """
        return await self.repo.get_activity_stats(days)
    
    # ==================== МАССОВЫЕ ОПЕРАЦИИ ====================
    
    async def prepare_mass_operation(
        self,
        min_level: Optional[int] = None,
        max_level: Optional[int] = None,
        active_last_days: Optional[int] = None,
        include_banned: bool = False
    ) -> Dict:
        """
        Подготовить массовую операцию - получить список пользователей.
        
        Args:
            min_level: Минимальный уровень
            max_level: Максимальный уровень
            active_last_days: Активны последние N дней
            include_banned: Включать забаненных
            
        Returns:
            Dict с количеством пользователей
        """
        min_last_activity = None
        if active_last_days:
            from datetime import datetime, timedelta
            min_last_activity = (datetime.now() - timedelta(days=active_last_days)).isoformat()
        
        user_ids = await self.repo.get_users_for_mass_operation(
            min_level=min_level,
            max_level=max_level,
            min_last_activity=min_last_activity,
            is_banned=include_banned
        )
        
        return {
            "success": True,
            "total_users": len(user_ids),
            "user_ids": user_ids[:100],  # Возвращаем только первые 100 для предпросмотра
            "filters": {
                "min_level": min_level,
                "max_level": max_level,
                "active_last_days": active_last_days,
                "include_banned": include_banned
            }
        }
    
    async def mass_give_item(
        self,
        user_ids: List[int],
        item_key: str,
        quantity: int,
        admin_id: int
    ) -> Dict:
        """
        Массовая выдача предмета.
        
        Args:
            user_ids: Список ID пользователей
            item_key: Ключ предмета
            quantity: Количество
            admin_id: ID админа
            
        Returns:
            Dict с результатом
        """
        # Валидация
        if quantity < 1 or quantity > 100:
            return {"success": False, "error": "Количество должно быть от 1 до 100"}
        
        if len(user_ids) > 10000:
            return {"success": False, "error": "Максимум 10000 пользователей за раз"}
        
        # Требуется подтверждение для больших операций
        if len(user_ids) > 100:
            confirmation = get_confirmation_service()
            token = await confirmation.request_confirmation(
                user_id=admin_id,
                action="mass_give_item",
                data={
                    "user_count": len(user_ids),
                    "item_key": item_key,
                    "quantity": quantity
                }
            )
            return {
                "success": False,
                "requires_confirmation": True,
                "token": token,
                "message": f"⚠️ Требуется подтверждение для {len(user_ids)} пользователей"
            }
        
        return await self.repo.mass_give_item(
            user_ids=user_ids,
            item_key=item_key,
            quantity=quantity,
            admin_id=admin_id
        )
        
    async def mass_add_resources(
        self,
        user_ids: List[int],
        resources: Dict[str, int],
        admin_id: int
    ) -> Dict:
        """
        Массовое начисление ресурсов.
        
        Args:
            user_ids: Список ID пользователей
            resources: Dict с ресурсами для добавления
            admin_id: ID админа
            
        Returns:
            Dict с результатом
        """
        # Валидация
        for key, value in resources.items():
            if value < 0:
                return {"success": False, "error": f"Значение {key} должно быть положительным"}
            if value > 10**9:
                return {"success": False, "error": f"Значение {key} слишком большое (макс. 10^9)"}
        
        if len(user_ids) > 10000:
            return {"success": False, "error": "Максимум 10000 пользователей за раз"}
        
        # Требуется подтверждение для больших операций
        if len(user_ids) > 100:
            confirmation = get_confirmation_service()
            token = await confirmation.request_confirmation(
                user_id=admin_id,
                action="mass_add_resources",
                data={
                    "user_count": len(user_ids),
                    "resources": resources
                }
            )
            return {
                "success": False,
                "requires_confirmation": True,
                "token": token,
                "message": f"⚠️ Требуется подтверждение для {len(user_ids)} пользователей"
            }
        
        return await self.repo.mass_add_resources(
            user_ids=user_ids,
            resources=resources,
            admin_id=admin_id
        )
    
    # ==================== ЛОГИ ====================
    
    async def get_logs(
        self,
        limit: int = 50,
        page: int = 1,
        admin_id: Optional[int] = None,
        action: Optional[str] = None,
        target_user_id: Optional[int] = None
    ) -> Dict:
        """
        Получить логи действий админов.
        
        Args:
            limit: Количество записей
            page: Номер страницы
            admin_id: Фильтр по админу
            action: Фильтр по действию
            target_user_id: Фильтр по цели
            
        Returns:
            Dict с логами
        """
        offset = (page - 1) * limit
        
        logs = await self.repo.get_admin_logs(
            limit=limit,
            admin_id=admin_id,
            action=action,
            target_user_id=target_user_id,
            offset=offset
        )
        
        return {
            "success": True,
            "logs": logs,
            "page": page,
            "has_more": len(logs) == limit
        }
    
    # ==================== ПРАВА ====================
    
    async def check_permission(self, user_id: int, permission: str) -> bool:
        """
        Проверить право доступа.
        
        Args:
            user_id: ID пользователя
            permission: Право для проверки
            
        Returns:
            bool
        """
        role = await self.get_admin_role(user_id)
        
        if not role:
            return False
        
        if role == "owner":
            return True
        
        permissions = self.ROLE_PERMISSIONS.get(role, [])
        return permission in permissions or "all" in permissions
    
    async def get_admin_role(self, user_id: int, use_cache: bool = True) -> Optional[str]:
        """
        Получить роль админа.
        
        Args:
            user_id: ID пользователя
            use_cache: Использовать кэш
            
        Returns:
            str - роль или None
        """
        if use_cache:
            cached = await self.cache.get(f"admin_role:{user_id}")
            if cached:
                return cached
        
        role = await self.repo.get_admin_role(user_id)
        
        if role and use_cache:
            await self.cache.set(f"admin_role:{user_id}", role)
        
        return role
    
    async def is_admin(self, user_id: int) -> bool:
        """
        Проверить, является ли пользователь админом.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool
        """
        return await self.repo.is_admin(user_id)
    
    # ==================== ПРЕСЕТЫ ====================
    
    PRESETS = {
        "starter_pack": {
            "name": "🎁 Стартовый набор",
            "description": "Базовый набор для нового игрока",
            "items": [
                ("container_common", 3),
                ("container_rare", 1),
            ],
            "resources": {
                "metal": 5000,
                "crystals": 100
            }
        },
        "event_reward": {
            "name": "🎉 Награда за ивент",
            "description": "Награда за участие в событии",
            "items": [
                ("container_epic", 2),
                ("container_legendary", 1),
            ],
            "resources": {
                "metal": 50000,
                "crystals": 5000,
                "dark_matter": 50
            }
        },
        "compensation": {
            "name": "⚖️ Компенсация",
            "description": "Компенсация за баги/проблемы",
            "items": [
                ("container_rare", 5),
                ("container_epic", 2)
            ],
            "resources": {
                "metal": 25000,
                "crystals": 2500,
                "dark_matter": 25
            }
        },
        "premium_gift": {
            "name": "⭐ Премиум подарок",
            "description": "Особый подарок от администрации",
            "items": [
                ("container_mythic", 1),
                ("container_epic", 3),
                ("container_rare", 5),
            ],
            "resources": {
                "metal": 100000,
                "crystals": 10000,
                "dark_matter": 100
            }
        },
        "weekly_bonus": {
            "name": "📅 Еженедельный бонус",
            "description": "Бонус за активность",
            "items": [
                ("container_rare", 2),
                ("container_epic", 1),
            ],
            "resources": {
                "metal": 15000,
                "crystals": 1500
            }
        },
        "test_reward": {
            "name": "🧪 Тестовая награда",
            "description": "Для тестирования функций",
            "items": [
                ("container_common", 1),
            ],
            "resources": {
                "metal": 100,
                "crystals": 10
            }
        }
    }
    
    async def apply_preset(
        self,
        preset_id: str,
        user_id: int,
        admin_id: int
    ) -> Dict:
        """
        Применить пресет к игроку.
        
        Args:
            preset_id: ID пресета
            user_id: ID пользователя
            admin_id: ID админа
            
        Returns:
            Dict с результатом
        """
        preset = self.PRESETS.get(preset_id)
        
        if not preset:
            return {"success": False, "error": "Пресет не найден"}
        
        results = {
            "items": [],
            "resources": None,
            "errors": []
        }
        
        # Выдаём предметы
        for item_key, quantity in preset.get("items", []):
            result = await self.give_item(
                user_id=user_id,
                item_key=item_key,
                quantity=quantity,
                admin_id=admin_id
            )
            
            if result.get("success"):
                results["items"].append({"item_key": item_key, "quantity": quantity})
            else:
                results["errors"].append(f"Ошибка выдачи {item_key}: {result.get('error')}")
        
        # Выдаём ресурсы
        resources = preset.get("resources")
        if resources:
            result = await self.update_player_resources(
                user_id=user_id,
                resources=resources,
                admin_id=admin_id
            )
            
            if result.get("success"):
                results["resources"] = resources
            else:
                results["errors"].append(f"Ошибка выдачи ресурсов: {result.get('error')}")
        
        # Логируем
        await self.repo.log_action(
            admin_id=admin_id,
            action="apply_preset",
            target_user_id=user_id,
            details=f"Preset: {preset_id} ({preset['name']})"
        )
        
        return {
            "success": len(results["errors"]) == 0,
            "preset_id": preset_id,
            "preset_name": preset["name"],
            "results": results
        }
    
    def get_presets_list(self) -> List[Dict]:
        """
        Получить список доступных пресетов.
        
        Returns:
            List[Dict] - список пресетов
        """
        return [
            {
                "id": preset_id,
                "name": preset_data["name"],
                "description": preset_data.get("description", ""),
                "items": preset_data.get("items", []),
                "resources": preset_data.get("resources", {})
            }
            for preset_id, preset_data in self.PRESETS.items()
        ]
    
    def get_preset(self, preset_id: str) -> Optional[Dict]:
        """
        Получить данные пресета по ID.
        
        Args:
            preset_id: ID пресета
            
        Returns:
            Dict с данными пресета или None
        """
        preset = self.PRESETS.get(preset_id)
        if not preset:
            return None
        
        return {
            "id": preset_id,
            "name": preset["name"],
            "description": preset.get("description", ""),
            "items": preset.get("items", []),
            "resources": preset.get("resources", {})
        }
    
    # ==================== ВСПОМОГАТЕЛЬНЫЕ ====================
    
    async def give_item(
        self,
        user_id: int,
        item_key: str,
        quantity: int,
        admin_id: int
    ) -> Dict:
        """
        Выдать любой предмет игроку.
        
        Args:
            user_id: ID пользователя
            item_key: Ключ предмета
            quantity: Количество
            admin_id: ID админа
            
        Returns:
            Dict с результатом
        """
        # Проверяем существование игрока
        player = await self.repo.get_player(user_id)
        if not player:
            return {"success": False, "error": "Игрок не найден"}
        
        # Выдаём
        result = await self.repo.give_item(
            user_id=user_id,
            item_key=item_key,
            quantity=quantity,
            admin_id=admin_id
        )
        
        if result.get("success"):
            await self.cache.invalidate_player(user_id)
        
        return result


class ConfirmationService:
    """
    Сервис подтверждения опасных действий.
    
    Хранит временные токены подтверждения.
    """
    
    CONFIRMATION_TIMEOUT = 60  # секунд
    
    def __init__(self):
        self._pending: Dict[str, Dict] = {}
    
    async def request_confirmation(
        self,
        user_id: int,
        action: str,
        data: Dict
    ) -> str:
        """
        Запросить подтверждение действия.
        
        Args:
            user_id: ID админа
            action: Действие
            data: Данные действия
            
        Returns:
            str - токен подтверждения
        """
        import secrets
        token = secrets.token_urlsafe(16)
        
        self._pending[token] = {
            "user_id": user_id,
            "action": action,
            "data": data,
            "expires_at": datetime.now() + timedelta(seconds=self.CONFIRMATION_TIMEOUT)
        }
        
        return token
    
    async def check_confirmation(self, token: str, user_id: int) -> Dict:
        """
        Проверить подтверждение.
        
        Args:
            token: Токен подтверждения
            user_id: ID админа
            
        Returns:
            Dict с данными или ошибкой
        """
        pending = self._pending.get(token)
        
        if not pending:
            return {"valid": False, "error": "Токен не найден"}
        
        if pending["user_id"] != user_id:
            return {"valid": False, "error": "Неверный пользователь"}
        
        if datetime.now() > pending["expires_at"]:
            del self._pending[token]
            return {"valid": False, "error": "Время подтверждения истекло"}
        
        # Удаляем использованный токен
        del self._pending[token]
        
        return {
            "valid": True,
            "action": pending["action"],
            "data": pending["data"]
        }
    
    async def cancel_confirmation(self, token: str):
        """Отменить подтверждение"""
        self._pending.pop(token, None)


# Глобальные экземпляры
_cache_service = None
_admin_service = None
_confirmation_service = None


def get_cache_service() -> AdminCacheService:
    """Получить экземпляр сервиса кэширования"""
    global _cache_service
    if _cache_service is None:
        _cache_service = AdminCacheService()
    return _cache_service


def get_admin_service(db_path: str) -> AdminService:
    """
    Получить экземпляр сервиса админ-панели.
    
    Args:
        db_path: Путь к БД
        
    Returns:
        AdminService
    """
    global _admin_service
    if _admin_service is None:
        repo = AdminRepository(db_path)
        _admin_service = AdminService(repo)
    return _admin_service


def get_confirmation_service() -> ConfirmationService:
    """Получить экземпляр сервиса подтверждений"""
    global _confirmation_service
    if _confirmation_service is None:
        _confirmation_service = ConfirmationService()
    return _confirmation_service
