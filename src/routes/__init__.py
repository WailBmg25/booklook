from .base import base_router
from .book_routes import book_router
from .auth_routes import auth_router, user_router
from .review_routes import review_router
from .reading_progress_routes import progress_router

__all__ = [
    "base_router",
    "book_router",
    "auth_router",
    "user_router",
    "review_router",
    "progress_router"
]