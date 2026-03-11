"""
Core - Ядро системы
Технические компоненты бота
"""

from .cache import cache, CacheManager
from .worker import worker, BackgroundWorker
from .security import (
    CallbackSecurityMiddleware,
    OwnershipMiddleware,
    create_safe_callback,
    is_safe_callback
)
from .rate_limiter import (
    rate_limiter,
    anti_spam,
    click_protector,
    RateLimiter,
    ActionType,
    AntiSpamMiddleware,
    ClickSpeedProtector
)

__all__ = [
    # Cache
    'cache',
    'CacheManager',
    
    # Worker
    'worker',
    'BackgroundWorker',
    
    # Security
    'CallbackSecurityMiddleware',
    'OwnershipMiddleware',
    'create_safe_callback',
    'is_safe_callback',
    
    # Rate Limiter
    'rate_limiter',
    'anti_spam',
    'click_protector',
    'RateLimiter',
    'ActionType',
    'AntiSpamMiddleware',
    'ClickSpeedProtector',
]
