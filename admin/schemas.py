"""
Pydantic модели для валидации данных в админ-панели
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum


class ResourceType(str, Enum):
    """Типы ресурсов"""
    METAL = "metal"
    CRYSTALS = "crystals"
    DARK_MATTER = "dark_matter"
    CREDITS = "credits"
    QUANTUM_TOKENS = "quantum_tokens"


class ContainerType(str, Enum):
    """Типы контейнеров"""
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    MYTHIC = "mythic"
    LEGENDARY = "legendary"
    KSM = "ksm"


class ModuleRarity(str, Enum):
    """Редкость модулей"""
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    MYTHIC = "mythic"
    LEGENDARY = "legendary"


class BanDuration(str, Enum):
    """Длительность бана"""
    HOUR_1 = "1h"
    HOURS_24 = "24h"
    DAYS_7 = "7d"
    FOREVER = "forever"
    CUSTOM = "custom"


# ===== СХЕМЫ ДЛЯ ИГРОКОВ =====

class ResourceUpdateSchema(BaseModel):
    """Схема валидации изменения ресурсов"""
    metal: int = Field(0, ge=0, le=10**12, description="Количество металла")
    crystals: int = Field(0, ge=0, le=10**12, description="Количество кристаллов")
    dark_matter: int = Field(0, ge=0, le=10**9, description="Количество тёмной материи")
    credits: int = Field(0, ge=0, le=10**12, description="Количество кредитов")
    
    @validator('metal', 'crystals', 'dark_matter', 'credits')
    def validate_positive(cls, v):
        if v < 0:
            raise ValueError('Значение не может быть отрицательным')
        return v


class ResourceSingleUpdateSchema(BaseModel):
    """Схема валидации изменения одного ресурса"""
    resource_type: ResourceType
    value: int = Field(..., ge=0, le=10**12)
    user_id: int = Field(..., ge=1)
    
    @validator('value')
    def validate_value(cls, v):
        if v > 10**12:
            raise ValueError('Слишком большое значение')
        return v


class PlayerSearchSchema(BaseModel):
    """Схема валидации поиска игрока"""
    query: str = Field(..., min_length=3, max_length=100)
    
    @validator('query')
    def sanitize_query(cls, v):
        # Удаляем потенциально опасные символы
        return v.strip().replace(';', '').replace('--', '')


class PlayerCardSchema(BaseModel):
    """Схема данных карточки игрока"""
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    level: int = 1
    prestige: int = 0
    metal: int = 0
    crystals: int = 0
    dark_matter: int = 0
    credits: int = 0
    quantum_tokens: int = 0
    is_banned: bool = False
    created_at: Optional[str] = None
    last_activity: Optional[str] = None
    
    class Config:
        from_attributes = True


# ===== СХЕМЫ ДЛЯ ВЫДАЧИ =====

class GiveContainerSchema(BaseModel):
    """Схема валидации выдачи контейнера"""
    user_id: int = Field(..., ge=1, description="ID пользователя")
    container_type: ContainerType = Field(..., description="Тип контейнера")
    quantity: int = Field(1, ge=1, le=100, description="Количество")
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v > 100:
            raise ValueError('Максимум 100 контейнеров за раз')
        return v


class GiveMaterialSchema(BaseModel):
    """Схема валидации выдачи материала"""
    user_id: int = Field(..., ge=1)
    material_key: str = Field(..., min_length=3, max_length=50)
    quantity: int = Field(1, ge=1, le=1000)
    
    @validator('material_key')
    def validate_material_key(cls, v):
        # Только буквы, цифры и подчёркивание
        if not v.replace('_', '').isalnum():
            raise ValueError('Недопустимые символы в ключе материала')
        return v


class GiveModuleSchema(BaseModel):
    """Схема валидации выдачи модуля"""
    user_id: int = Field(..., ge=1)
    rarity: ModuleRarity = Field(..., description="Редкость модуля")
    name: Optional[str] = Field(None, max_length=100)


# ===== СХЕМЫ ДЛЯ БАНА =====

class BanPlayerSchema(BaseModel):
    """Схема валидации бана игрока"""
    user_id: int = Field(..., ge=1)
    reason: str = Field(..., min_length=1, max_length=500, description="Причина бана")
    duration: Optional[BanDuration] = Field(None, description="Длительность")
    custom_hours: Optional[int] = Field(None, ge=1, le=8760, description="Кастомное время в часах")
    
    @validator('reason')
    def sanitize_reason(cls, v):
        # Удаляем HTML теги
        import re
        return re.sub(r'<[^>]+>', '', v)


class UnbanPlayerSchema(BaseModel):
    """Схема валидации разбана игрока"""
    user_id: int = Field(..., ge=1)
    reason: Optional[str] = Field(None, max_length=500)


# ===== СХЕМЫ ДЛЯ МАССОВЫХ ОПЕРАЦИЙ =====

class MassOperationSchema(BaseModel):
    """Схема валидации массовых операций"""
    operation_type: str = Field(..., description="Тип операции")
    target_condition: Optional[str] = Field(None, description="Условие выборки")
    value: int = Field(..., ge=1, description="Значение")
    
    @validator('operation_type')
    def validate_operation_type(cls, v):
        allowed = ['give_container', 'give_material', 'add_resources']
        if v not in allowed:
            raise ValueError(f'Недопустимый тип операции. Разрешены: {allowed}')
        return v


# ===== СХЕМЫ ДЛЯ ЛОГОВ =====

class AdminLogSchema(BaseModel):
    """Схема лога действия админа"""
    log_id: int
    admin_id: int
    action: str
    target_user_id: Optional[int] = None
    details: Optional[str] = None
    created_at: str
    
    class Config:
        from_attributes = True


class AdminLogFilterSchema(BaseModel):
    """Схема фильтрации логов"""
    admin_id: Optional[int] = None
    action: Optional[str] = None
    target_user_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = Field(50, ge=1, le=200)


# ===== СХЕМЫ ДЛЯ НАСТРОЕК =====

class SettingUpdateSchema(BaseModel):
    """Схема обновления настройки"""
    key: str = Field(..., min_length=3, max_length=100)
    value: Dict = Field(..., description="Значение настройки в формате JSON")
    
    @validator('key')
    def validate_key(cls, v):
        if not v.replace('_', '').isalnum():
            raise ValueError('Недопустимые символы в ключе')
        return v


class RarityChancesSchema(BaseModel):
    """Схема шансов редкости"""
    common: float = Field(70.0, ge=0, le=100)
    rare: float = Field(20.0, ge=0, le=100)
    epic: float = Field(7.0, ge=0, le=100)
    mythic: float = Field(2.5, ge=0, le=100)
    legendary: float = Field(0.5, ge=0, le=100)
    
    @validator('*')
    def validate_sum(cls, v, values):
        # Проверяем, что сумма примерно 100%
        total = sum(values.values()) if values else 0
        if total > 0 and abs(total - 100) > 0.1:
            raise ValueError(f'Сумма шансов должна быть 100%, сейчас: {total}%')
        return v


# ===== СХЕМЫ ДЛЯ ПРЕСЕТОВ =====

class PresetApplySchema(BaseModel):
    """Схема применения пресета"""
    preset_id: str = Field(..., description="ID пресета")
    user_id: int = Field(..., ge=1)


# ===== СХЕМЫ ОТВЕТОВ =====

class SuccessResponse(BaseModel):
    """Успешный ответ"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Dict] = None


class ErrorResponse(BaseModel):
    """Ответ с ошибкой"""
    success: bool = False
    error: str
    details: Optional[Dict] = None


class PlayerHistoryResponse(BaseModel):
    """Ответ с историей игрока"""
    user_id: int
    events: List[Dict]
    total_count: int
    page: int
    has_more: bool
