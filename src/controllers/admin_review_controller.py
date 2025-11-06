"""Admin review controller for review moderation operations."""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from repositories import ReviewRepository
from models import Review
from helpers import ResponseHelper
from controllers.base_controller import BaseController


class AdminReviewController(BaseController):
    """Controller for admin review moderation operations."""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.review_repo = ReviewRepository(db)
    
    def get_reviews_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        is_flagged: Optional[bool] = None,
        book_id: Optional[int] = None,
        user_id: Optional[int] = None,
        min_rating: Optional[int] = None,
        max_rating: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get paginated list of reviews with filtering."""
        # Validate pagination
        pagination_result = self.validate_pagination(page, page_size)
        if pagination_result["error"]:
            return pagination_result["response"]
        
        page, page_size = pagination_result["page"], pagination_result["page_size"]
        
        # Build query
        query = self.db.query(Review)
        
        # Apply filters
        if is_flagged is not None:
            query = query.filter(Review.is_flagged == is_flagged)
        
        if book_id is not None:
            query = query.filter(Review.book_id == book_id)
        
        if user_id is not None:
            query = query.filter(Review.user_id == user_id)
        
        if min_rating is not None:
            query = query.filter(Review.rating >= min_rating)
        
        if max_rating is not None:
            query = query.filter(Review.rating <= max_rating)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        reviews = query.order_by(desc(Review.created_at)).offset(offset).limit(page_size).all()
        
        # Calculate pagination metadata
        total_pages = (total_count + page_size - 1) // page_size
        
        return {
            "reviews": [review.to_dict(include_user=True, include_book=True) for review in reviews],
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": page,
            "page_size": page_size,
            "has_next": page < total_pages,
            "has_previous": page > 1
        }
    
    def get_flagged_reviews(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get flagged reviews for moderation queue."""
        return self.get_reviews_paginated(
            page=page,
            page_size=page_size,
            is_flagged=True
        )
    
    def flag_review(self, review_id: int) -> Dict[str, Any]:
        """Flag a review for moderation."""
        review = self.review_repo.get_by_id(review_id)
        
        if not review:
            return ResponseHelper.error_response("Review not found", code="REVIEW_NOT_FOUND")
        
        if review.is_flagged:
            return ResponseHelper.error_response("Review is already flagged", code="ALREADY_FLAGGED")
        
        review.is_flagged = True
        self.db.commit()
        
        return {
            "success": True,
            "message": "Review flagged successfully",
            "review": review.to_dict(include_user=True, include_book=True)
        }
    
    def unflag_review(self, review_id: int) -> Dict[str, Any]:
        """Unflag a review (approve it)."""
        review = self.review_repo.get_by_id(review_id)
        
        if not review:
            return ResponseHelper.error_response("Review not found", code="REVIEW_NOT_FOUND")
        
        review.is_flagged = False
        self.db.commit()
        
        return {
            "success": True,
            "message": "Review approved successfully",
            "review": review.to_dict(include_user=True, include_book=True)
        }
    
    def delete_review(self, review_id: int) -> Dict[str, Any]:
        """Delete a review."""
        review = self.review_repo.get_by_id(review_id)
        
        if not review:
            return ResponseHelper.error_response("Review not found", code="REVIEW_NOT_FOUND")
        
        book_id = review.book_id
        
        # Delete review
        self.db.delete(review)
        self.db.commit()
        
        # Update book rating statistics
        self._update_book_rating_stats(book_id)
        
        return {
            "success": True,
            "message": "Review deleted successfully"
        }
    
    def bulk_delete_reviews(self, review_ids: list[int]) -> Dict[str, Any]:
        """Bulk delete multiple reviews."""
        deleted_count = 0
        book_ids = set()
        
        for review_id in review_ids:
            review = self.review_repo.get_by_id(review_id)
            if review:
                book_ids.add(review.book_id)
                self.db.delete(review)
                deleted_count += 1
        
        self.db.commit()
        
        # Update book rating statistics for affected books
        for book_id in book_ids:
            self._update_book_rating_stats(book_id)
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "total_requested": len(review_ids)
        }
    
    def bulk_flag_reviews(self, review_ids: list[int]) -> Dict[str, Any]:
        """Bulk flag multiple reviews."""
        flagged_count = 0
        
        for review_id in review_ids:
            review = self.review_repo.get_by_id(review_id)
            if review and not review.is_flagged:
                review.is_flagged = True
                flagged_count += 1
        
        self.db.commit()
        
        return {
            "success": True,
            "flagged_count": flagged_count,
            "total_requested": len(review_ids)
        }
    
    def bulk_approve_reviews(self, review_ids: list[int]) -> Dict[str, Any]:
        """Bulk approve multiple reviews."""
        approved_count = 0
        
        for review_id in review_ids:
            review = self.review_repo.get_by_id(review_id)
            if review and review.is_flagged:
                review.is_flagged = False
                approved_count += 1
        
        self.db.commit()
        
        return {
            "success": True,
            "approved_count": approved_count,
            "total_requested": len(review_ids)
        }
    
    def _update_book_rating_stats(self, book_id: int) -> None:
        """Update book rating statistics after review changes."""
        from models import Book
        
        book = self.db.query(Book).filter(Book.id == book_id).first()
        if not book:
            return
        
        # Get all reviews for this book
        reviews = self.review_repo.get_reviews_by_book(book_id)
        
        if not reviews:
            book.average_rating = 0.0
            book.review_count = 0
        else:
            total_rating = sum(review.rating for review in reviews)
            book.average_rating = total_rating / len(reviews)
            book.review_count = len(reviews)
        
        self.db.commit()
        
        # Invalidate cache
        self.cache_helper.invalidate_book_cache(book_id)
