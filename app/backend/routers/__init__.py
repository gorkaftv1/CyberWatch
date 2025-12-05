from .auth import router as auth_router
from .dashboard import router as dashboard_router
from .incidents import router as incidents_router
from .users import router as users_router

__all__ = ["auth_router", "dashboard_router", "incidents_router", "users_router"]