from .base import base_router
from .book_routes import book_router
from .book_page_routes import router as book_page_router
from .auth_routes import auth_router, user_router
from .review_routes import review_router
from .reading_progress_routes import progress_router
from .admin_book_routes import router as admin_book_router
from .admin_user_routes import router as admin_user_router
from .admin_review_routes import router as admin_review_router
from .admin_analytics_routes import router as admin_analytics_router
from .admin_csv_routes import router as admin_csv_router

__all__ = [
    "base_router",
    "book_router",
    "book_page_router",
    "auth_router",
    "user_router",
    "review_router",
    "progress_router",
    "admin_book_router",
    "admin_user_router",
    "admin_review_router",
    "admin_analytics_router",
    "admin_csv_router"
]