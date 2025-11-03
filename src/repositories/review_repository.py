"""Review repository for review-related database operations."""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from models import Review, User, Book
from .base_repository import BaseRepository


class ReviewRepository(BaseRepository[Review]):
    """Repository for review data access operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, Review)
    
    def create_review(
        self,
        user_id: int,
        book_id: int,
        rating: int,
        title: Optional[str] = None,
        content: Optional[str] = None
    ) -> Review:
        """Create a new review."""
        review = Review(
            user_id=user_id,
            book_id=book_id,
            rating=rating,
            title=title,
            content=content,
            # Legacy fields for backward compatibility
            livre_id=book_id,
            note=rating,
            commentaire=content
        )
        
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review
    
    def find_user_review_for_book(self, user_id: int, book_id: int) -> Optional[Review]:
        """Find user's review for a specific book."""
        return self.db.query(Review).filter(
            and_(Review.user_id == user_id, Review.book_id == book_id)
        ).first()
    
    def user_has_reviewed_book(self, user_id: int, book_id: int) -> bool:
        """Check if user has already reviewed a book."""
        return self.find_user_review_for_book(user_id, book_id) is not None
    
    def get_book_reviews(
        self,
        book_id: int,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """Get reviews for a book with pagination."""
        query = self.db.query(Review).filter(Review.book_id == book_id)
        
        # Apply sorting
        if sort_by == "rating":
            sort_column = Review.rating
        elif sort_by == "created_at":
            sort_column = Review.created_at
        else:
            sort_column = Review.created_at
        
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        reviews = query.offset(offset).limit(page_size).all()
        
        total_pages = (total_count + page_size - 1) // page_size
        
        return {
            "items": reviews,
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": page,
            "page_size": page_size,
            "has_next": page < total_pages,
            "has_previous": page > 1
        }
    
    def get_user_reviews(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """Get reviews by a user with pagination."""
        query = self.db.query(Review).filter(Review.user_id == user_id)
        query = query.order_by(desc(Review.created_at))
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        reviews = query.offset(offset).limit(page_size).all()
        
        total_pages = (total_count + page_size - 1) // page_size
        
        return {
            "items": reviews,
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": page,
            "page_size": page_size,
            "has_next": page < total_pages,
            "has_previous": page > 1
        }
    
    def update_review(
        self,
        review_id: int,
        user_id: int,
        rating: Optional[int] = None,
        title: Optional[str] = None,
        content: Optional[str] = None
    ) -> Optional[Review]:
        """Update an existing review (only by the owner)."""
        review = self.db.query(Review).filter(
            and_(Review.id == review_id, Review.user_id == user_id)
        ).first()
        
        if not review:
            return None
        
        # Update fields
        if rating is not None:
            review.rating = rating
            review.note = rating  # Update legacy field
        
        if title is not None:
            review.title = title
        
        if content is not None:
            review.content = content
            review.commentaire = content  # Update legacy field
        
        self.db.commit()
        self.db.refresh(review)
        return review
    
    def delete_user_review(self, review_id: int, user_id: int) -> bool:
        """Delete a review (only by the owner)."""
        review = self.db.query(Review).filter(
            and_(Review.id == review_id, Review.user_id == user_id)
        ).first()
        
        if not review:
            return False
        
        self.db.delete(review)
        self.db.commit()
        return True
    
    def get_review_with_user_and_book(self, review_id: int) -> Optional[Dict[str, Any]]:
        """Get review with related user and book information."""
        review = self.get_by_id(review_id)
        if not review:
            return None
        
        user = self.db.query(User).filter(User.id == review.user_id).first()
        book = self.db.query(Book).filter(Book.id == review.book_id).first()
        
        return {
            "review": review,
            "user": user,
            "book": book
        }
    
    def get_rating_distribution(self, book_id: int) -> Dict[int, int]:
        """Get rating distribution for a book."""
        result = (
            self.db.query(Review.rating, func.count(Review.id))
            .filter(Review.book_id == book_id)
            .group_by(Review.rating)
            .all()
        )
        
        # Initialize distribution with zeros
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        # Fill in actual counts
        for rating, count in result:
            distribution[rating] = count
        
        return distribution
    
    def calculate_book_rating_stats(self, book_id: int) -> Tuple[float, int]:
        """Calculate average rating and review count for a book."""
        result = (
            self.db.query(
                func.avg(Review.rating).label('avg_rating'),
                func.count(Review.id).label('review_count')
            )
            .filter(Review.book_id == book_id)
            .first()
        )
        
        avg_rating = float(result.avg_rating) if result.avg_rating else 0.0
        review_count = result.review_count or 0
        
        return avg_rating, review_count
    
    def get_recent_reviews(self, limit: int = 10) -> List[Review]:
        """Get most recent reviews across all books."""
        return (
            self.db.query(Review)
            .order_by(desc(Review.created_at))
            .limit(limit)
            .all()
        )
    
    def get_top_rated_reviews(self, limit: int = 10) -> List[Review]:
        """Get highest rated reviews."""
        return (
            self.db.query(Review)
            .filter(Review.rating == 5)
            .order_by(desc(Review.created_at))
            .limit(limit)
            .all()
        )
    
    def get_reviews_by_rating(self, rating: int, limit: int = 10) -> List[Review]:
        """Get reviews with specific rating."""
        return (
            self.db.query(Review)
            .filter(Review.rating == rating)
            .order_by(desc(Review.created_at))
            .limit(limit)
            .all()
        )
    
    def get_book_review_summary(self, book_id: int) -> Dict[str, Any]:
        """Get comprehensive review summary for a book."""
        avg_rating, review_count = self.calculate_book_rating_stats(book_id)
        rating_distribution = self.get_rating_distribution(book_id)
        
        # Get recent reviews
        recent_reviews = (
            self.db.query(Review)
            .filter(Review.book_id == book_id)
            .order_by(desc(Review.created_at))
            .limit(5)
            .all()
        )
        
        return {
            "average_rating": avg_rating,
            "review_count": review_count,
            "rating_distribution": rating_distribution,
            "recent_reviews": recent_reviews
        }
    
    def delete_all_book_reviews(self, book_id: int) -> int:
        """Delete all reviews for a book (admin operation)."""
        count = self.db.query(Review).filter(Review.book_id == book_id).count()
        self.db.query(Review).filter(Review.book_id == book_id).delete()
        self.db.commit()
        return count
    
    def delete_all_user_reviews(self, user_id: int) -> int:
        """Delete all reviews by a user (admin operation)."""
        count = self.db.query(Review).filter(Review.user_id == user_id).count()
        self.db.query(Review).filter(Review.user_id == user_id).delete()
        self.db.commit()
        return count