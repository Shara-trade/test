"""
Репозиторий для работы с БД в админ-панели
Единый класс для всех операций с базой данных
"""
import aiosqlite
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json


class AdminRepository:
    """
    Репозиторий для работы с БД админ-панели.
    
    Отвечает за все операции с базой данных:
    - Получение и поиск игроков
    - Изменение ресурсов
    - Выдача предметов
    - Логирование действий
    - Получение статистики
    
    Attributes:
        db_path (str): Путь к файлу базы данных
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    # ==================== ИГРОКИ ====================
    
    async def get_player(self, user_id: int) -> Optional[Dict]:
        """
        Получить данные игрока по ID.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Dict с данными игрока или None
        """
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def search_players(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Поиск игроков по ID или username.
        
        Args:
            query: Поисковый запрос (ID или username)
            limit: Максимальное количество результатов
            
        Returns:
            List[Dict] - список найденных игроков
        """
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            
            # Пробуем как ID
            if query.isdigit():
                async with conn.execute(
                    "SELECT * FROM users WHERE user_id = ?",
                    (int(query),)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return [dict(row)]
            
            # Поиск по username (регистронезависимый)
            search_pattern = f"%{query}%"
            async with conn.execute(
                """SELECT * FROM users 
                   WHERE LOWER(username) LIKE LOWER(?) 
                      OR LOWER(first_name) LIKE LOWER(?)
                      OR LOWER(last_name) LIKE LOWER(?)
                   LIMIT ?""",
                (search_pattern, search_pattern, search_pattern, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]
    
    async def get_player_card_data(self, user_id: int) -> Optional[Dict]:
        """
        Получить полные данные для карточки игрока.
        Оптимизированный запрос с JOIN.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Dict с данными игрока и статистикой
        """
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            
            # Один сложный запрос вместо нескольких простых
            async with conn.execute("""
                SELECT 
                    u.*,
                    (SELECT COUNT(*) FROM inventory 
                     WHERE user_id = u.user_id AND item_key LIKE 'container_%' AND quantity > 0
                    ) as containers_count,
                    (SELECT COUNT(*) FROM modules WHERE user_id = u.user_id) as modules_count,
                    (SELECT COALESCE(SUM(quantity), 0) FROM inventory 
                     WHERE user_id = u.user_id AND item_key IN 
                     (SELECT item_key FROM items WHERE item_type = 'material')
                    ) as materials_count,
                    (SELECT COUNT(*) FROM drones WHERE user_id = u.user_id AND is_active = 1) as drones_count
                FROM users u
                WHERE u.user_id = ?
            """, (user_id,)) as cursor:
                row = await cursor.fetchone()
                
                if not row:
                    return None
                
                data = dict(row)
                # Преобразуем булевы значения
                data["is_banned"] = bool(data.get("is_banned", 0))
                data["is_admin"] = bool(data.get("is_admin", 0))
                
                return data
    
    async def update_resources(
        self, 
        user_id: int, 
        admin_id: int,
        resources: Dict[str, int],
        log_details: str = None
    ) -> bool:
        """
        Обновить ресурсы игрока (установить абсолютное значение).
        
        Args:
            user_id: ID пользователя
            admin_id: ID админа
            resources: Dict с новыми значениями ресурсов
            log_details: Описание для лога
            
        Returns:
            bool - успех операции
        """
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                # Получаем текущие значения
                conn.row_factory = aiosqlite.Row
                async with conn.execute(
                    "SELECT metal, crystals, dark_matter, credits FROM users WHERE user_id = ?",
                    (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if not row:
                        return False
                    old_values = dict(row)
                
                # Вычисляем разницу
                updates = []
                values = []
                changes = []
                
                for key, new_value in resources.items():
                    if new_value is not None:
                        diff = new_value - old_values.get(key, 0)
                        updates.append(f"{key} = ?")
                        values.append(new_value)
                        changes.append(f"{key}: {old_values.get(key, 0)} -> {new_value}")
                
                if not updates:
                    return True
                
                values.append(user_id)
                
                # Обновляем
                await conn.execute(
                    f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?",
                    values
                )
                
                # Логируем
                details = log_details or "; ".join(changes)
                await conn.execute(
                    """INSERT INTO admin_logs (admin_id, action, target_user_id, details)
                       VALUES (?, 'edit_resource', ?, ?)""",
                    (admin_id, user_id, details)
                )
                
                await conn.commit()
                return True
                
            except Exception as e:
                print(f"Error updating resources: {e}")
                return False
    
    async def give_item(
        self, 
        user_id: int, 
        item_key: str, 
        quantity: int,
        admin_id: int
    ) -> Dict:
        """
        Выдать предмет игроку.
        
        Args:
            user_id: ID пользователя
            item_key: Ключ предмета
            quantity: Количество
            admin_id: ID админа
            
        Returns:
            Dict с результатом операции
        """
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                # Проверяем существование предмета в каталоге
                async with conn.execute(
                    "SELECT 1 FROM items WHERE item_key = ?",
                    (item_key,)
                ) as cursor:
                    if not await cursor.fetchone():
                        # Предмет не найден в каталоге, но можно выдать
                        # (для контейнеров и других служебных предметов)
                        pass
                
                # Проверяем, есть ли уже такой предмет
                conn.row_factory = aiosqlite.Row
                async with conn.execute(
                    "SELECT item_id, quantity FROM inventory WHERE user_id = ? AND item_key = ?",
                    (user_id, item_key)
                ) as cursor:
                    row = await cursor.fetchone()
                
                if row:
                    # Увеличиваем количество
                    new_quantity = row["quantity"] + quantity
                    await conn.execute(
                        "UPDATE inventory SET quantity = ? WHERE item_id = ?",
                        (new_quantity, row["item_id"])
                    )
                else:
                    # Добавляем новый предмет
                    await conn.execute(
                        "INSERT INTO inventory (user_id, item_key, quantity) VALUES (?, ?, ?)",
                        (user_id, item_key, quantity)
                    )
                
                # Логируем
                await conn.execute(
                    """INSERT INTO admin_logs (admin_id, action, target_user_id, details)
                       VALUES (?, 'give_item', ?, ?)""",
                    (admin_id, user_id, f"{item_key} x{quantity}")
                )
                
                await conn.commit()
                
                return {"success": True, "item_key": item_key, "quantity": quantity}
                
            except Exception as e:
                print(f"Error giving item: {e}")
                return {"success": False, "error": str(e)}
    
    async def ban_player(
        self, 
        user_id: int, 
        admin_id: int,
        reason: str,
        duration_hours: Optional[int] = None
    ) -> Dict:
        """
        Забанить игрока.
        
        Args:
            user_id: ID пользователя
            admin_id: ID админа
            reason: Причина бана
            duration_hours: Длительность в часах (None = навсегда)
            
        Returns:
            Dict с результатом операции
        """
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                # Проверяем существование игрока
                async with conn.execute(
                    "SELECT 1 FROM users WHERE user_id = ?",
                    (user_id,)
                ) as cursor:
                    if not await cursor.fetchone():
                        return {"success": False, "error": "Игрок не найден"}
                
                # Устанавливаем бан
                await conn.execute(
                    "UPDATE users SET is_banned = 1 WHERE user_id = ?",
                    (user_id,)
                )
                
                # Записываем в таблицу банов
                expires_at = None
                if duration_hours:
                    expires_at = (datetime.now() + timedelta(hours=duration_hours)).isoformat()
                
                await conn.execute(
                    """INSERT INTO bans (user_id, admin_id, reason, duration_hours, expires_at, status, created_at)
                       VALUES (?, ?, ?, ?, ?, 'active', CURRENT_TIMESTAMP)""",
                    (user_id, admin_id, reason, duration_hours, expires_at)
                )
                
                # Логируем
                duration_text = f"на {duration_hours} ч." if duration_hours else "навсегда"
                await conn.execute(
                    """INSERT INTO admin_logs (admin_id, action, target_user_id, details)
                       VALUES (?, 'ban_player', ?, ?)""",
                    (admin_id, user_id, f"{reason} ({duration_text})")
                )
                
                await conn.commit()
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "reason": reason,
                    "duration_hours": duration_hours,
                    "expires_at": expires_at
                }
                
            except Exception as e:
                print(f"Error banning player: {e}")
                return {"success": False, "error": str(e)}
    
    async def unban_player(self, user_id: int, admin_id: int) -> Dict:
        """
        Разбанить игрока.
        
        Args:
            user_id: ID пользователя
            admin_id: ID админа
            
        Returns:
            Dict с результатом операции
        """
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                # Снимаем бан
                await conn.execute(
                    "UPDATE users SET is_banned = 0 WHERE user_id = ?",
                    (user_id,)
                )
                
                # Обновляем статус в таблице банов
                await conn.execute(
                    """UPDATE bans SET status = 'cancelled', cancelled_by = ?, cancelled_at = CURRENT_TIMESTAMP
                       WHERE user_id = ? AND status = 'active'""",
                    (admin_id, user_id)
                )
                
                # Логируем
                await conn.execute(
                    """INSERT INTO admin_logs (admin_id, action, target_user_id, details)
                       VALUES (?, 'unban_player', ?, 'Разбанен')""",
                    (admin_id, user_id)
                )
                
                await conn.commit()
                
                return {"success": True, "user_id": user_id}
                
            except Exception as e:
                print(f"Error unbanning player: {e}")
                return {"success": False, "error": str(e)}
    
    # ==================== СТАТИСТИКА ====================
    
    async def get_admin_stats(self) -> Dict:
        """
        Получить статистику для админ-панели.
        
        Returns:
            Dict со статистикой
        """
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            
            stats = {}
            
            # Общее количество игроков
            async with conn.execute("SELECT COUNT(*) as count FROM users") as cursor:
                row = await cursor.fetchone()
                stats["total_players"] = row["count"] if row else 0
            
            # Активных сегодня
            async with conn.execute(
                """SELECT COUNT(*) as count FROM users 
                   WHERE DATE(last_activity) = DATE('now')"""
            ) as cursor:
                row = await cursor.fetchone()
                stats["active_today"] = row["count"] if row else 0
            
            # Онлайн сейчас (активность за 5 минут)
            async with conn.execute(
                """SELECT COUNT(*) as count FROM users 
                   WHERE datetime(last_activity) > datetime('now', '-5 minutes')"""
            ) as cursor:
                row = await cursor.fetchone()
                stats["online_now"] = row["count"] if row else 0
            
            # Забаненных
            async with conn.execute(
                "SELECT COUNT(*) as count FROM users WHERE is_banned = 1"
            ) as cursor:
                row = await cursor.fetchone()
                stats["banned_players"] = row["count"] if row else 0
            
            # Новых сегодня
            async with conn.execute(
                """SELECT COUNT(*) as count FROM users 
                   WHERE DATE(created_at) = DATE('now')"""
            ) as cursor:
                row = await cursor.fetchone()
                stats["new_players_today"] = row["count"] if row else 0
            
            # Новых за неделю
            async with conn.execute(
                """SELECT COUNT(*) as count FROM users 
                   WHERE DATE(created_at) >= DATE('now', '-7 days')"""
            ) as cursor:
                row = await cursor.fetchone()
                stats["new_players_week"] = row["count"] if row else 0
            
            # Экономика
            async with conn.execute(
                "SELECT COALESCE(SUM(metal), 0) as total_metal, COALESCE(SUM(crystals), 0) as total_crystals, COALESCE(SUM(credits), 0) as total_credits FROM users"
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    stats["total_metal"] = row["total_metal"]
                    stats["total_crystals"] = row["total_crystals"]
                    stats["total_credits"] = row["total_credits"]
            
            return stats
    
    async def get_realtime_stats(self) -> Dict:
        """
        Получить статистику в реальном времени.
        
        Returns:
            Dict с метриками в реальном времени
        """
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            
            # Онлайн сейчас
            async with conn.execute(
                """SELECT COUNT(*) FROM users 
                   WHERE datetime(last_activity) > datetime('now', '-5 minutes')"""
            ) as cursor:
                online_now = (await cursor.fetchone())[0]
            
            # Активных за час
            async with conn.execute(
                """SELECT COUNT(*) FROM users 
                   WHERE datetime(last_activity) > datetime('now', '-1 hour')"""
            ) as cursor:
                active_hour = (await cursor.fetchone())[0]
            
            # Добыто за час
            async with conn.execute(
                """SELECT COALESCE(SUM(total_mined), 0) FROM users 
                   WHERE datetime(last_activity) > datetime('now', '-1 hour')"""
            ) as cursor:
                mined_hour = (await cursor.fetchone())[0]
            
            return {
                "online_now": online_now,
                "active_hour": active_hour,
                "mined_hour": mined_hour or 0,
                "timestamp": datetime.now().isoformat()
            }
    
    # ==================== ЛОГИ ====================
    
    async def get_admin_logs(
        self, 
        limit: int = 50, 
        admin_id: Optional[int] = None,
        action: Optional[str] = None,
        target_user_id: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict]:
        """
        Получить логи действий админов.
        
        Args:
            limit: Максимальное количество записей
            admin_id: Фильтр по ID админа
            action: Фильтр по действию
            target_user_id: Фильтр по ID цели
            offset: Смещение для пагинации
            
        Returns:
            List[Dict] - список логов
        """
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            
            query = """
                SELECT 
                    al.*,
                    u.username as admin_username
                FROM admin_logs al
                LEFT JOIN users u ON al.admin_id = u.user_id
                WHERE 1=1
            """
            params = []
            
            if admin_id:
                query += " AND al.admin_id = ?"
                params.append(admin_id)
            
            if action:
                query += " AND al.action = ?"
                params.append(action)
            
            if target_user_id:
                query += " AND al.target_user_id = ?"
                params.append(target_user_id)
            
            query += " ORDER BY al.created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            async with conn.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]
    
    async def log_action(
        self, 
        admin_id: int, 
        action: str, 
        target_user_id: Optional[int] = None,
        details: Optional[str] = None
    ):
        """
        Записать действие админа в лог.
        
        Args:
            admin_id: ID админа
            action: Действие
            target_user_id: ID цели
            details: Детали
        """
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute(
                """INSERT INTO admin_logs (admin_id, action, target_user_id, details)
                   VALUES (?, ?, ?, ?)""",
                (admin_id, action, target_user_id, details)
            )
            await conn.commit()
    
    # ==================== ИСТОРИЯ ИГРОКА ====================
    
    async def get_player_history(
        self, 
        user_id: int, 
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict]:
        """
        Получить историю действий над игроком.
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество записей
            offset: Смещение для пагинации
            
        Returns:
            List[Dict] - список событий
        """
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            
            # Логи админов по этому игроку
            async with conn.execute("""
                SELECT 
                    al.created_at,
                    al.action,
                    al.details,
                    u.username as admin_name
                FROM admin_logs al
                LEFT JOIN users u ON al.admin_id = u.user_id
                WHERE al.target_user_id = ?
                ORDER BY al.created_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset)) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]
    
    # ==================== АДМИНЫ ====================
    
    async def is_admin(self, user_id: int) -> bool:
        """
        Проверить, является ли пользователь админом.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool
        """
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.execute(
                "SELECT 1 FROM admins WHERE user_id = ? AND is_active = 1",
                (user_id,)
            ) as cursor:
                return await cursor.fetchone() is not None
    
    async def get_admin_role(self, user_id: int) -> Optional[str]:
        """
        Получить роль админа.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            str - роль или None
        """
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT role FROM admins WHERE user_id = ? AND is_active = 1",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row["role"] if row else None
    
    async def get_all_admins(self) -> List[Dict]:
        """
        Получить список всех админов.
        
        Returns:
            List[Dict] - список админов
        """
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT 
                    a.*,
                    u.username
                FROM admins a
                LEFT JOIN users u ON a.user_id = u.user_id
                WHERE a.is_active = 1
                ORDER BY 
                CASE a.role
                    WHEN 'owner' THEN 1
                    WHEN 'senior' THEN 2
                    WHEN 'moderator' THEN 3
                    ELSE 4
                END
            """) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]
    
    async def add_admin(
        self, 
        user_id: int, 
        role: str, 
        added_by: int,
        permissions: Optional[Dict] = None
    ) -> Dict:
        """
        Добавить админа.
        
        Args:
            user_id: ID пользователя
            role: Роль
            added_by: ID добавившего админа
            permissions: Дополнительные права
            
        Returns:
            Dict с результатом
        """
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                permissions_json = json.dumps(permissions or {})
                
                await conn.execute(
                    """INSERT INTO admins (user_id, role, permissions, added_by, is_active)
                       VALUES (?, ?, ?, ?, 1)
                       ON CONFLICT(user_id) DO UPDATE SET 
                       role = excluded.role,
                       permissions = excluded.permissions,
                       is_active = 1""",
                    (user_id, role, permissions_json, added_by)
                )
                
                await conn.commit()
                
                return {"success": True, "user_id": user_id, "role": role}
                
            except Exception as e:
                print(f"Error adding admin: {e}")
                return {"success": False, "error": str(e)}
    
    async def remove_admin(self, user_id: int, removed_by: int) -> Dict:
        """
        Удалить админа (деактивировать).
        
        Args:
            user_id: ID пользователя
            removed_by: ID удалившего админа
            
        Returns:
            Dict с результатом
        """
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                await conn.execute(
                    "UPDATE admins SET is_active = 0 WHERE user_id = ?",
                    (user_id,)
                )
                
                await conn.commit()
                
                return {"success": True, "user_id": user_id}
                
            except Exception as e:
                print(f"Error removing admin: {e}")
                return {"success": False, "error": str(e)}
    
    # ==================== МОДУЛИ ====================
    
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
            module_data: Данные модуля (name, rarity, buffs, debuffs)
            admin_id: ID админа
            
        Returns:
            Dict с результатом
        """
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                cursor = await conn.execute(
                    """INSERT INTO modules (user_id, name, rarity, buffs, debuffs, slot, created_at)
                       VALUES (?, ?, ?, ?, ?, NULL, CURRENT_TIMESTAMP)""",
                    (
                        user_id,
                        module_data["name"],
                        module_data["rarity"],
                        json.dumps(module_data["buffs"]),
                        json.dumps(module_data["debuffs"])
                    )
                )
                
                module_id = cursor.lastrowid
                
                # Логируем
                await conn.execute(
                    """INSERT INTO admin_logs (admin_id, action, target_user_id, details)
                       VALUES (?, 'give_module', ?, ?)""",
                    (admin_id, user_id, f"Module #{module_id}: {module_data['name']}")
                )
                
                await conn.commit()
                
                return {
                    "success": True,
                    "module_id": module_id,
                    "name": module_data["name"]
                }
                
            except Exception as e:
                print(f"Error giving module: {e}")
                return {"success": False, "error": str(e)}
    
    async def get_modules_stats(self) -> Dict:
        """
        Получить статистику по модулям.
        
        Returns:
            Dict со статистикой
        """
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            
            stats = {}
            
            # Всего модулей
            async with conn.execute("SELECT COUNT(*) as count FROM modules") as cursor:
                row = await cursor.fetchone()
                stats["total_modules"] = row["count"] if row else 0
            
            # По редкости
            async with conn.execute(
                "SELECT rarity, COUNT(*) as count FROM modules GROUP BY rarity"
            ) as cursor:
                rows = await cursor.fetchall()
                stats["by_rarity"] = {r["rarity"]: r["count"] for r in rows}
            
            # Установленных
            async with conn.execute(
                "SELECT COUNT(*) as count FROM modules WHERE slot IS NOT NULL"
            ) as cursor:
                row = await cursor.fetchone()
                stats["installed"] = row["count"] if row else 0
            
            return stats
    
    # ==================== КОНТЕЙНЕРЫ ====================
    
    async def get_containers_stats(self) -> Dict:
        """
        Получить статистику по контейнерам.
        
        Returns:
            Dict со статистикой
        """
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            
            stats = {}
            
            # Всего контейнеров у игроков
            async with conn.execute(
                """SELECT COALESCE(SUM(quantity), 0) as total FROM inventory 
                   WHERE item_key LIKE 'container_%'"""
            ) as cursor:
                row = await cursor.fetchone()
                stats["total_containers"] = row["total"] if row else 0
            
            # По типам
            async with conn.execute(
                """SELECT item_key, COALESCE(SUM(quantity), 0) as count 
                   FROM inventory 
                   WHERE item_key LIKE 'container_%'
                   GROUP BY item_key"""
            ) as cursor:
                rows = await cursor.fetchall()
                stats["by_type"] = {r["item_key"]: r["count"] for r in rows}
            
            # Открыто за сегодня
            async with conn.execute(
                """SELECT COUNT(*) as count FROM containers 
                   WHERE status = 'opened' AND DATE(opened_at) = DATE('now')"""
            ) as cursor:
                row = await cursor.fetchone()
                stats["opened_today"] = row["count"] if row else 0
            
            return stats
    
    # ==================== НАСТРОЙКИ ====================
    
    async def get_setting(self, key: str) -> Optional[Any]:
        """
        Получить настройку из БД.
        
        Args:
            key: Ключ настройки
            
        Returns:
            Значение настройки или None
        """
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT setting_value FROM admin_settings WHERE setting_key = ?",
                (key,)
            ) as cursor:
                row = await cursor.fetchone()
                
                if not row:
                    return None
                
                try:
                    return json.loads(row["setting_value"])
                except:
                    return row["setting_value"]
    
    async def set_setting(self, key: str, value: Any, admin_id: Optional[int] = None) -> bool:
        """
        Установить настройку.
        
        Args:
            key: Ключ настройки
            value: Значение
            admin_id: ID админа
            
        Returns:
            bool - успех операции
        """
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                value_json = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
                
                await conn.execute(
                    """INSERT INTO admin_settings (setting_key, setting_value, updated_at, updated_by)
                       VALUES (?, ?, CURRENT_TIMESTAMP, ?)
                       ON CONFLICT(setting_key) DO UPDATE SET 
                       setting_value = excluded.setting_value,
                       updated_at = CURRENT_TIMESTAMP,
                       updated_by = excluded.updated_by""",
                    (key, value_json, admin_id)
                )
                
                await conn.commit()
                return True
                
            except Exception as e:
                print(f"Error setting setting: {e}")
                return False
    
    async def get_all_settings(self, category: Optional[str] = None) -> Dict:
        """
        Получить все настройки (опционально по категории).
        
        Args:
            category: Категория настроек
            
        Returns:
            Dict с настройками
        """
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            
            if category:
                query = "SELECT setting_key, setting_value FROM admin_settings WHERE category = ?"
                params = (category,)
            else:
                query = "SELECT setting_key, setting_value FROM admin_settings"
                params = ()
            
            async with conn.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                
                result = {}
                for row in rows:
                    try:
                        result[row["setting_key"]] = json.loads(row["setting_value"])
                    except:
                        result[row["setting_key"]] = row["setting_value"]
                
                return result
