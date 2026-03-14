"""
Handlers package
"""
from .start import router as start_router
from .mine import router as mine_router
from .profile import router as profile_router
from .inventory import router as inventory_router
from .modules import router as modules_router
from .drones import router as drones_router
from .top import router as top_router
from .help import router as help_router
from .market import router as market_router
from .craft import router as craft_router
from .clan import router as clan_router
from .galaxy import router as galaxy_router
from .admin_panel import router as admin_panel_router

__all__ = [
    'start_router',
    'mine_router',
    'profile_router',
    'inventory_router',
    'modules_router',
    'drones_router',
    'top_router',
    'help_router',
    'market_router',
    'craft_router',
    'clan_router',
    'galaxy_router',
    'admin_panel_router'
]