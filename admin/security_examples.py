"""
Примеры использования безопасности в админ-обработчиках
Показывает, как интегрировать декораторы, валидацию и подтверждения
"""

# ============================================================
# ПРИМЕР 1: Использование декоратора admin_required
# ============================================================

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from admin.decorators import admin_required, AdminFilter
from admin import is_admin, check_permission

router = Router()


# Вариант 1: Декоратор на функцию
@router.callback_query(F.data == "admin:players")
@admin_required("players")  # Требуется право "players"
async def admin_players_menu(callback: CallbackQuery):
    """Меню управления игроками"""
    # Код обработчика
    await callback.message.edit_text("👤 Меню игроков")


# Вариант 2: Фильтр в роутере
@router.callback_query(AdminFilter(permission="economy"))
async def admin_economy_menu(callback: CallbackQuery):
    """Меню экономики - только для админов с правом economy"""
    await callback.message.edit_text("💰 Меню экономики")


# Вариант 3: Ручная проверка в начале обработчика
@router.callback_query(F.data.startswith("admin:settings"))
async def admin_settings_menu(callback: CallbackQuery):
    """Меню настроек с ручной проверкой"""
    user_id = callback.from_user.id
    
    if not await is_admin(user_id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    if not await check_permission(user_id, "settings"):
        await callback.answer("⛔ Недостаточно прав", show_alert=True)
        return
    
    # Код обработчика
    await callback.message.edit_text("⚙️ Меню настроек")


# ============================================================
# ПРИМЕР 2: Валидация через Pydantic схемы
# ============================================================

from admin.schemas import (
    ResourceUpdateSchema, ResourceSingleUpdateSchema,
    GiveContainerSchema, BanPlayerSchema, PlayerSearchSchema
)
from pydantic import ValidationError


@router.message()
async def admin_search_player(message: Message, state: FSMContext):
    """Поиск игрока с валидацией"""
    query = message.text.strip()
    
    # Валидация через Pydantic
    try:
        schema = PlayerSearchSchema(query=query)
        validated_query = schema.query
    except ValidationError as e:
        await message.answer(f"❌ Ошибка: {e.errors()[0]['msg']}")
        return
    
    # Используем валидированные данные
    # ... поиск в БД по validated_query


@router.callback_query(F.data.startswith("admin:confirm:res:"))
async def admin_confirm_resource_change(callback: CallbackQuery):
    """Подтверждение изменения ресурса с валидацией"""
    parts = callback.data.split(":")
    user_id = int(parts[3])
    resource = parts[4]
    new_value = int(parts[5])
    
    # Валидация
    try:
        schema = ResourceSingleUpdateSchema(
            resource_type=resource,
            value=new_value,
            user_id=user_id
        )
    except ValidationError as e:
        await callback.answer(
            f"❌ Неверные данные: {e.errors()[0]['msg']}", 
            show_alert=True
        )
        return
    
    # Выполняем изменение
    # ... код обновления ресурса


# ============================================================
# ПРИМЕР 3: Подтверждение опасных действий
# ============================================================

from admin import get_confirmation_service, get_admin_service
from config import DATABASE_PATH


@router.callback_query(F.data.startswith("admin:players:ban:"))
async def admin_ban_player_start(callback: CallbackQuery, state: FSMContext):
    """Начало процесса бана с подтверждением"""
    user_id = int(callback.data.split(":")[3])
    
    # Проверяем права
    if not await check_permission(callback.from_user.id, "players"):
        await callback.answer("⛔ Недостаточно прав", show_alert=True)
        return
    
    # Проверяем, что не баним owner
    target_role = await get_admin_service(DATABASE_PATH).get_admin_role(user_id)
    if target_role == "owner":
        await callback.answer("⛔ Нельзя забанить владельца", show_alert=True)
        return
    
    # Запрашиваем подтверждение
    confirmation_service = get_confirmation_service()
    token = await confirmation_service.request_confirmation(
        user_id=callback.from_user.id,
        action="ban_player",
        data={"target_user_id": user_id}
    )
    
    # Показываем предупреждение
    text = (
        "⚠️ <b>ПОДТВЕРЖДЕНИЕ БАНА</b>\n\n"
        f"Вы собираетесь забанить игрока ID: {user_id}\n\n"
        "Это действие нельзя отменить!"
    )
    
    from admin.safe_keyboards import SafeKeyboardBuilder
    keyboard = (
        SafeKeyboardBuilder(callback.from_user.id)
        .row(
            ("✅ Подтвердить бан", f"admin:ban:confirm:{token}"),
            ("❌ Отмена", f"admin:ban:cancel:{token}")
        )
        .build()
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')


@router.callback_query(F.data.startswith("admin:ban:confirm:"))
async def admin_ban_confirm(callback: CallbackQuery):
    """Подтверждение бана"""
    token = callback.data.split(":")[3]
    
    # Проверяем токен подтверждения
    confirmation_service = get_confirmation_service()
    result = await confirmation_service.check_confirmation(
        token=token,
        user_id=callback.from_user.id
    )
    
    if not result.get("valid"):
        await callback.answer(
            f"❌ {result.get('error', 'Ошибка подтверждения')}", 
            show_alert=True
        )
        return
    
    # Выполняем бан
    target_user_id = result["data"]["target_user_id"]
    service = get_admin_service(DATABASE_PATH)
    
    ban_result = await service.ban_player(
        user_id=target_user_id,
        reason="Забанен через админ-панель",
        admin_id=callback.from_user.id,
        duration="forever"
    )
    
    if ban_result.get("success"):
        await callback.answer("✅ Игрок забанен", show_alert=True)
    else:
        await callback.answer(f"❌ Ошибка: {ban_result.get('error')}", show_alert=True)


@router.callback_query(F.data.startswith("admin:ban:cancel:"))
async def admin_ban_cancel(callback: CallbackQuery):
    """Отмена бана"""
    token = callback.data.split(":")[3]
    
    confirmation_service = get_confirmation_service()
    await confirmation_service.cancel_confirmation(token)
    
    await callback.answer("❌ Бан отменён")
    # Возврат к карточке игрока


# ============================================================
# ПРИМЕР 4: Подключение middleware в main.py
# ============================================================

"""
# В main.py:

from admin import get_rate_limit_middleware, get_audit_middleware
from config import DATABASE_PATH

# Создаём middleware
rate_limit_mw = get_rate_limit_middleware()
audit_mw = get_audit_middleware(DATABASE_PATH)

# Подключаем к dispatcher
dp.callback_query.middleware(rate_limit_mw)
dp.callback_query.middleware(audit_mw)

# Или только для admin роутера:
admin_router.callback_query.middleware(rate_limit_mw)
admin_router.callback_query.middleware(audit_mw)
"""


# ============================================================
# ПРИМЕР 5: Использование безопасных клавиатур
# ============================================================

from admin.safe_keyboards import SafeKeyboardBuilder, make_safe_keyboard


async def show_player_card_safe(user_id: int, target_user_id: int):
    """Показать карточку игрока с безопасной клавиатурой"""
    
    # Вариант 1: Через SafeKeyboardBuilder
    keyboard = (
        SafeKeyboardBuilder(user_id)
        .row(
            ("💰 Изменить ресурсы", f"admin:players:resources:{target_user_id}"),
            ("📦 Выдать контейнер", f"admin:players:give_container:{target_user_id}")
        )
        .row(
            ("🚫 Бан игрока", f"admin:players:ban:{target_user_id}"),
            ("📜 История", f"admin:players:history:{target_user_id}")
        )
        .back_button("admin:players")
        .close_button()
        .build()
    )
    
    return keyboard


async def show_confirmation_keyboard(user_id: int, confirm_data: str, cancel_data: str):
    """Показать клавиатуру подтверждения"""
    
    # Вариант 2: Через make_safe_keyboard
    keyboard = make_safe_keyboard(
        user_id=user_id,
        buttons=[
            [
                ("✅ Подтвердить", confirm_data),
                ("❌ Отмена", cancel_data)
            ]
        ]
    )
    
    return keyboard


# ============================================================
# ПРИМЕР 6: Полный обработчик с валидацией
# ============================================================

@router.callback_query(F.data.startswith("admin:players:give_container:"))
async def admin_give_container_safe(callback: CallbackQuery, state: FSMContext):
    """Выдача контейнера с полной валидацией и проверками"""
    
    # 1. Проверка прав
    if not await check_permission(callback.from_user.id, "players"):
        await callback.answer("⛔ Недостаточно прав", show_alert=True)
        return
    
    # 2. Парсинг данных
    parts = callback.data.split(":")
    user_id = int(parts[3])
    container_type = parts[4]
    quantity = int(parts[5]) if len(parts) > 5 else 1
    
    # 3. Валидация через Pydantic
    try:
        from admin.schemas import GiveContainerSchema
        schema = GiveContainerSchema(
            user_id=user_id,
            container_type=container_type,
            quantity=quantity
        )
    except ValidationError as e:
        await callback.answer(
            f"❌ Неверные данные: {e.errors()[0]['msg']}", 
            show_alert=True
        )
        return
    
    # 4. Проверка лимитов (опционально)
    if quantity > 50:
        # Требуется подтверждение для больших количеств
        confirmation_service = get_confirmation_service()
        token = await confirmation_service.request_confirmation(
            user_id=callback.from_user.id,
            action="give_container",
            data={
                "target_user_id": user_id,
                "container_type": container_type,
                "quantity": quantity
            }
        )
        
        text = f"⚠️ Выдать {quantity} контейнеров? Это много!"
        keyboard = (
            SafeKeyboardBuilder(callback.from_user.id)
            .confirm_buttons(
                f"admin:give_container:confirm:{token}",
                f"admin:players:card:{user_id}"
            )
            .build()
        )
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        return
    
    # 5. Выполнение операции
    service = get_admin_service(DATABASE_PATH)
    result = await service.give_container(
        user_id=schema.user_id,
        container_type=schema.container_type.value,
        quantity=schema.quantity,
        admin_id=callback.from_user.id
    )
    
    # 6. Ответ
    if result.get("success"):
        await callback.answer(
            f"✅ Выдано {quantity} {container_type} контейнеров", 
            show_alert=True
        )
    else:
        await callback.answer(
            f"❌ Ошибка: {result.get('error')}", 
            show_alert=True
        )
