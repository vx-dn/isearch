"""API routes module initialization."""

from .auth import router as auth_router
from .health import router as health_router
from .receipts import router as receipt_router
from .search import router as search_router

__all__ = ["health_router", "auth_router", "receipt_router", "search_router"]
