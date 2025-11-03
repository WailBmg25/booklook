"""Review controller for review-related business logic."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from repositories import ReviewRepository, BookRepository
from models import Review
from helpers import CacheHelper, ValidationHelper


class ReviewController:
    """Controller for review business logic operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.review_repo = ReviewRepository(db)
        self.book_repo = BookRepository(db)
        self.cache_helper = CacheHelper()
    
    def create_review(
        self,
        user_id: int,
        book_id: int,
        rating: int,
        title: Optional[str] = None,
        content: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a new review with business logic validation."""
        # Validate review data
        validation_result = ValidationHelper.validate_review_data(rating, title, content)
        if not validation_result["is_valid"]:
            return {"error": "Invalid review data", "issues": validation_result["issues"]}
        
        # Sanitize input
        title = ValidationHelper.sanitize_string(title, 200)
        content = ValidationHelper.sanitize_string(content, 5000)
        
        # Check if user already reviewed this book
        if self.review_repo.user_has_reviewed_book(user_id, book_id):
            return {"error": "User has already reviewed this book"}
        
        # Create review using repository
        review = self.review_repo.create_review(
            user_id=user_id,
            book_id=book_id,
            rating=rating,
            title=title,
            content=content
        )
        
        # Update legacy fields using model business logic
        review.update_legacy_fields()
        self.db.commit()
        
        # Update book's rating statistics
        self._update_book_rating_stats(book_id)
        
        # Invalidate caches
        self._invalidate_review_caches(book_id)
        
        # Get review with related data
        review_data = self.review_repo.get_review_with_user_and_book(review.id)
        if not review_data:
            return None
        
        # Use model business logic for response
        return review_data["review"].to_dict(include_user=True, include_book=True)
    
    def update_review(
        self,
        review_id: int,
        user_id: int,
        rating: Optional[int] = None,
        title: Optional[str] = None,
        content: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update an existing review with business logic validation."""
        # Validate review data if provided
        if rating is not None or title is not None or content is not None:
            validation_result = ValidationHelper.validate_review_data(
                rating or 5, title, content  # Use 5 as default for validation if rating not provided
            )
            if not validation_result["is_valid"]:
                return {"error": "Invalid review data", "issues": validation_result["issues"]}
        
        # Sanitize input
        title = ValidationHelper.sanitize_string(title, 200) if title is not None else None
        content = ValidationHelper.sanitize_string(content, 5000) if content is not None else None
        
        # Update review using repository
        review = self.review_repo.update_review(
            review_id=review_id,
            user_id=user_id,
            rating=rating,
            title=title,
            content=content
        )
        
        if not review:
            return None
        
        # Update legacy fields using model business logic
        review.update_legacy_fields()
        self.db.commit()
        
        # Update book's rating statistics
        self._update_book_rating_stats(review.book_id)
        
        # Invalidate caches
        self._invalidate_review_caches(review.book_id)
        
        # Get review with related data
        review_data = self.review_repo.get_review_with_user_and_book(review.id)
        if not review_data:
            return None
        
        return review_data["review"].to_dict(include_user=True, include_book=True)
    
    def delete_review(self, review_id: int, user_id: int) -> bool:
        """Delete a review with business logic."""
        # Get review first to get book_id for cache invalidation
        review = self.review_repo.get_by_id(review_id)
        if not review or review.user_id != user_id:
            return False
        
        book_id = review.book_id
        
        # Delete using repository
        success = self.review_repo.delete_user_review(review_id, user_id)
        
        if success:
            # Update book's rating statistics
            self._update_book_rating_stats(book_id)
            
            # Invalidate caches
            self._invalidate_review_caches(book_id)
        
        return success
    
    def get_review_details(self, review_id: int) -> Optional[Dict[str, Any]]:
        """Get review details with related information."""
        review_data = self.review_repo.get_review_with_user_and_book(review_id)
        if not review_data:
            return None
        
        # Use model business logic for response
        return review_data["review"].to_dict(include_user=True, include_book=True)
    
    def get_book_reviews(
        self,
        book_id: int,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """Get reviews for a book with pagination."""
        # Validate parameters
        pagination_validation = ValidationHelper.validate_pagination(page, page_size)
        if not pagination_validation["is_valid"]:
            return {"error": "Invalid pagination parameters", "issues": pagination_validation["issues"]}
        
        sort_validation = ValidationHelper.validate_sort_params(
            sort_by, sort_order, ["created_at", "rating", "updated_at"]
        )
        if not sort_validation["is_valid"]:
            return {"error": "Invalid sort parameters", "issues": sort_validation["issues"]}
        
        # Use validated parameters
        page = pagination_validation["page"]
        page_size = pagination_validation["page_size"]
        sort_by = sort_validation["sort_by"]
        sort_order = sort_validation["sort_order"]
        
        result = self.review_repo.get_book_reviews(
            book_id=book_id,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Convert reviews using model business logic
        reviews_list = []
        for review in result["items"]:
            review_data = self.review_repo.get_review_with_user_and_book(review.id)
            if review_data:
                reviews_list.append(review_data["review"].to_dict(include_user=True))
        
        return {
            "reviews": reviews_list,
            "total_count": result["total_count"],
            "total_pages": result["total_pages"],
            "current_page": result["current_page"],
            "page_size": result["page_size"],
            "has_next": result["has_next"],
            "has_previous": result["has_previous"]
        }
    
    def get_user_reviews(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """Get reviews by a user with pagination."""
        # Validate pagination
        pagination_validation = ValidationHelper.validate_pagination(page, page_size)
        if not pagination_validation["is_valid"]:
            return {"error": "Invalid pagination parameters", "issues": pagination_validation["issues"]}
        
        page = pagination_validation["page"]
        page_size = pagination_validation["page_size"]
        
        result = self.review_repo.get_user_reviews(
            user_id=user_id,
            page=page,
            page_size=page_size
        )
        
        # Convert reviews using model business logic
        reviews_list = []
        for review in result["items"]:
            review_data = self.review_repo.get_review_with_user_and_book(review.id)
            if review_data:
                reviews_list.append(review_data["review"].to_dict(include_book=True))
        
        return {
            "reviews": reviews_list,
            "total_count": result["total_count"],
            "total_pages": result["total_pages"],
            "current_page": result["current_page"],
            "page_size": result["page_size"],
            "has_next": result["has_next"],
            "has_previous": result["has_previous"]
        }
    
    def get_user_review_for_book(self, user_id: int, book_id: int) -> Optional[Dict[str, Any]]:
        """Get user's review for a specific book."""
        review = self.review_repo.find_user_review_for_book(user_id, book_id)
        if not review:
            return None
        
        # Use model business logic for response
        return review.to_dict()
    
    def get_rating_distribution(self, book_id: int) -> Dict[int, int]:
        """Get rating distribution for a book with caching."""
        cache_key = self.cache_helper.generate_cache_key("rating_dist", book_id=book_id)
        
        # Try cache first
        cached_data = self.cache_helper.get(cache_key)
        if cached_data:
            return cached_data
        
        # Get from repository
        distribution = self.review_repo.get_rating_distribution(book_id)
        
        # Cache the result
        self.cache_helper.set(cache_key, distribution, ttl=1800)  # 30 minutes
        
        return distribution
    
    def get_book_review_summary(self, book_id: int) -> Dict[str, Any]:
        """Get comprehensive review summary for a book."""
        summary = self.review_repo.get_book_review_summary(book_id)
        
        # Convert recent reviews using model business logic
        recent_reviews = []
        for review in summary["recent_reviews"]:
            review_data = self.review_repo.get_review_with_user_and_book(review.id)
            if review_data:
                recent_reviews.append(review_data["review"].to_dict(include_user=True))
        
        return {
            "average_rating": summary["average_rating"],
            "review_count": summary["review_count"],
            "rating_distribution": summary["rating_distribution"],
            "recent_reviews": recent_reviews
        }
    
    def get_recent_reviews(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent reviews across all books."""
        reviews = self.review_repo.get_recent_reviews(limit)
        
        # Convert using model business logic
        reviews_list = []
        for review in reviews:
            review_data = self.review_repo.get_review_with_user_and_book(review.id)
            if review_data:
                review_dict = review_data["review"].to_dict(include_user=True, include_book=True)
                # Truncate content for recent reviews list
                if review_dict.get("content"):
                    review_dict["content"] = review.get_content_preview(200)
                reviews_list.append(review_dict)
        
        return reviews_list
    
    def get_top_rated_reviews(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get highest rated reviews."""
        reviews = self.review_repo.get_top_rated_reviews(limit)
        
        # Convert using model business logic
        reviews_list = []
        for review in reviews:
            review_data = self.review_repo.get_review_with_user_and_book(review.id)
            if review_data:
                reviews_list.append(review_data["review"].to_dict(include_user=True, include_book=True))
        
        return reviews_list
    
    def validate_review_data(self, rating: int, title: Optional[str], content: Optional[str]) -> Dict[str, Any]:
        """Validate review data using helper."""
        return ValidationHelper.validate_review_data(rating, title, content)
    
    def _update_book_rating_stats(self, book_id: int) -> None:
        """Update book's rating statistics using business logic."""
        avg_rating, review_count = self.review_repo.calculate_book_rating_stats(book_id)
        
        # Update book using repository
        self.book_repo.update_rating_stats(book_id, avg_rating, review_count)
    
    def _invalidate_review_caches(self, book_id: int) -> None:
        """Invalidate review-related caches."""
        # Invalidate rating distribution cache
        rating_cache_key = self.cache_helper.generate_cache_key("rating_dist", book_id=book_id)
        self.cache_helper.delete(rating_cache_key)
        
        # Invalidate book caches
        self.cache_helper.invalidate_book_cache(book_id)