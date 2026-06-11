from .search import router as search_router
from .deputies import router as deputies_router
from .seances import router as seances_router
from .legislatives import router as legislatives_router
from .stats import router as stats_router

__all__ = [
    "search_router",
    "deputies_router", 
    "seances_router",
    "legislatives_router",
    "stats_router"
]