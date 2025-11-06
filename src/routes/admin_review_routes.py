"""Admin review moderation routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field

from database import get_db
from controllers.admin_review_controller import AdminReviewController
from middleware import require_admin
from models import User


router = APIRouter(prefix="/admin/reviews", tags=["Admin - Reviews"])


# Request/Response Models
class BulkReviewRequest(BaseModel):
    """Request model for bulk review operations."""
    review_ids: List[int] = Field(..., min_items=1)


@router.get("")
async def get_reviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_flagged: Optional[bool] = Query(None),
    book_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    min_rating: Optional[int] = Query(None, ge=1, le=5),
    max_rating: Optional[int] = Query(None, ge=1, le=5),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Get paginated list of reviews with filtering (Admin only)."""
    controller = AdminReviewController(db)
    return controller.get_reviews_paginated(
        page=page,
        page_size=page_size,
        is_flagged=is_flagged,
        book_id=book_id,
        user_id=user_id,
        min_rating=min_rating,
        max_rating=max_rating
    )


@router.get("/flagged")
async def get_flagged_reviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Get flagged reviews for moderation queue (Admin only)."""
    controller = AdminReviewController(db)
    return controller.get_flagged_reviews(page, page_size)


@router.put("/{review_id}/flag")
async def flag_review(
    review_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Flag a review for moderation (Admin only)."""
    controller = AdminReviewController(db)
    result = controller.flag_review(review_id)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Failed to flag review")
        )
    
    return result


@router.put("/{review_id}/approve")
async def approve_review(
    review_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Approve a flagged review (Admin only)."""
    controller = AdminReviewController(db)
    result = controller.unflag_review(review_id)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Failed to approve review")
        )
    
    return result


@router.delete("/{review_id}")
async def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Delete a review (Admin only)."""
    controller = AdminReviewController(db)
    result = controller.delete_review(review_id)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=404,
            detail=result.get("message", "Review not found")
        )
    
    return result


@router.post("/bulk-delete")
async def bulk_delete_reviews(
    request: BulkReviewRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Bulk delete multiple reviews (Admin only)."""
    controller = AdminReviewController(db)
    return controller.bulk_delete_reviews(request.review_ids)


@router.post("/bulk-flag")
async def bulk_flag_reviews(
    request: BulkReviewRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Bulk flag multiple reviews (Admin only)."""
    controller = AdminReviewController(db)
    return controller.bulk_flag_reviews(request.review_ids)


@router.post("/bulk-approve")
async def bulk_approve_reviews(
    request: BulkReviewRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Bulk approve multiple reviews (Admin only)."""
    controller = AdminReviewController(db)
    return controller.bulk_approve_reviews(request.review_ids)
