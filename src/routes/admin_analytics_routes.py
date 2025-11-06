"""Admin analytics and logging routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from controllers.admin_analytics_controller import AdminAnalyticsController
from middleware import require_admin
from models import User


router = APIRouter(prefix="/admin/analytics", tags=["Admin - Analytics"])


@router.get("/overview")
async def get_overview_analytics(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Get overview analytics with key system metrics (Admin only)."""
    controller = AdminAnalyticsController(db)
    return controller.get_overview_analytics()


@router.get("/users")
async def get_user_analytics(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Get user activity analytics (Admin only)."""
    controller = AdminAnalyticsController(db)
    return controller.get_user_analytics()


@router.get("/books")
async def get_book_analytics(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Get book popularity and statistics (Admin only)."""
    controller = AdminAnalyticsController(db)
    return controller.get_book_analytics()


@router.get("/reviews")
async def get_review_analytics(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Get review statistics and trends (Admin only)."""
    controller = AdminAnalyticsController(db)
    return controller.get_review_analytics()


@router.get("/logs")
async def get_admin_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    action_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Get admin action logs (Admin only)."""
    controller = AdminAnalyticsController(db)
    return controller.get_admin_logs(page, page_size, action_type)
