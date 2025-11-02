"""Review service for managing book reviews and ratings."""

from typing import List, Optional, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from models.book import Review, Book, User
from helpers.redis_client import get_redis_client
import json
from datetime import datetime


class ReviewService:
    """Service for review management and rating calculations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.redis_client = get_redis_client()
    
    def create_review(
        self,
        user_id: int,
        book_id: int,
        rating: int,
        title: Optional[str] = None,
        content: Optional[str] = None
    ) -> Optional[Dict]:
        """Create a new review for a book."""
        # Validate rating
        if rating < 1 or rating > 5:
            return None
        
        # Check if user and book exist
        user = self.db.query(User).filter(User.id == user_id).first()
        book = self.db.query(Book).filter(Book.id == book_id).first()
        
        if not user or not book:
            return None
        
        # Check if user already reviewed this book
        existing_review = self.db.query(Review).filter(
            and_(Review.user_id == user_id, Review.book_id == book_id)
        ).first()
        
        if existing_review:
            return None  # User already reviewed this book
        
        # Create review
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
        
        # Update book's average rating and review count
        self._update_book_rating_stats(book_id)
        
        # Invalidate caches
        self._invalidate_review_caches(book_id)
        
        return {
            "id": review.id,
            "user_id": review.user_id,
            "book_id": review.book_id,
            "rating": review.rating,
            "title": review.title,
            "content": review.content,
            "created_at": review.created_at,
            "updated_at": review.updated_at,
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "photo_url": user.photo_url
            }
        }
    
    def update_review(
        self,
        review_id: int,
        user_id: int,
        rating: Optional[int] = None,
        title: Optional[str] = None,
        content: Optional[str] = None
    ) -> Optional[Dict]:
        """Update an existing review."""
        review = self.db.query(Review).filter(
            and_(Review.id == review_id, Review.user_id == user_id)
        ).first()
        
        if not review:
            return None
        
        # Validate rating if provided
        if rating is not None and (rating < 1 or rating > 5):
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
        
        # Update book's average rating and review count
        self._update_book_rating_stats(review.book_id)
        
        # Invalidate caches
        self._invalidate_review_caches(review.book_id)
        
        # Get user info
        user = self.db.query(User).filter(User.id == review.user_id).first()
        
        return {
            "id": review.id,
            "user_id": review.user_id,
            "book_id": review.book_id,
            "rating": review.rating,
            "title": review.title,
            "content": review.content,
            "created_at": review.created_at,
            "updated_at": review.updated_at,
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "photo_url": user.photo_url
            } if user else None
        }
    
    def delete_review(self, review_id: int, user_id: int) -> bool:
        """Delete a review."""
        review = self.db.query(Review).filter(
            and_(Review.id == review_id, Review.user_id == user_id)
        ).first()
        
        if not review:
            return False
        
        book_id = review.book_id
        
        self.db.delete(review)
        self.db.commit()
        
        # Update book's average rating and review count
        self._update_book_rating_stats(book_id)
        
        # Invalidate caches
        self._invalidate_review_caches(book_id)
        
        return True
    
    def get_review_by_id(self, review_id: int) -> Optional[Dict]:
        """Get a review by ID."""
        review = self.db.query(Review).filter(Review.id == review_id).first()
        if not review:
            return None
        
        user = self.db.query(User).filter(User.id == review.user_id).first()
        book = self.db.query(Book).filter(Book.id == review.book_id).first()
        
        return {
            "id": review.id,
            "user_id": review.user_id,
            "book_id": review.book_id,
            "rating": review.rating,
            "title": review.title,
            "content": review.content,
            "created_at": review.created_at,
            "updated_at": review.updated_at,
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "photo_url": user.photo_url
            } if user else None,
            "book": {
                "id": book.id,
                "titre": book.titre,
                "author_names": book.author_names or []
            } if book else None
        }
    
    def get_book_reviews(
        self,
        book_id: int,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[Dict], int, int]:
        """Get reviews for a book with pagination."""
        # Build query
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
        
        # Convert to dict format with user info
        reviews_list = []
        for review in reviews:
            user = self.db.query(User).filter(User.id == review.user_id).first()
            
            review_dict = {
                "id": review.id,
                "user_id": review.user_id,
                "book_id": review.book_id,
                "rating": review.rating,
                "title": review.title,
                "content": review.content,
                "created_at": review.created_at,
                "updated_at": review.updated_at,
                "user": {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "photo_url": user.photo_url
                } if user else None
            }
            reviews_list.append(review_dict)
        
        total_pages = (total_count + page_size - 1) // page_size
        
        return reviews_list, total_count, total_pages
    
    def get_user_reviews(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[Dict], int, int]:
        """Get reviews by a user with pagination."""
        query = self.db.query(Review).filter(Review.user_id == user_id)
        query = query.order_by(desc(Review.created_at))
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        reviews = query.offset(offset).limit(page_size).all()
        
        # Convert to dict format with book info
        reviews_list = []
        for review in reviews:
            book = self.db.query(Book).filter(Book.id == review.book_id).first()
            
            review_dict = {
                "id": review.id,
                "user_id": review.user_id,
                "book_id": review.book_id,
                "rating": review.rating,
                "title": review.title,
                "content": review.content,
                "created_at": review.created_at,
                "updated_at": review.updated_at,
                "book": {
                    "id": book.id,
                    "titre": book.titre,
                    "author_names": book.author_names or [],
                    "image_url": book.image_url
                } if book else None
            }
            reviews_list.append(review_dict)
        
        total_pages = (total_count + page_size - 1) // page_size
        
        return reviews_list, total_count, total_pages
    
    def get_user_review_for_book(self, user_id: int, book_id: int) -> Optional[Dict]:
        """Get user's review for a specific book."""
        review = self.db.query(Review).filter(
            and_(Review.user_id == user_id, Review.book_id == book_id)
        ).first()
        
        if not review:
            return None
        
        return {
            "id": review.id,
            "user_id": review.user_id,
            "book_id": review.book_id,
            "rating": review.rating,
            "title": review.title,
            "content": review.content,
            "created_at": review.created_at,
            "updated_at": review.updated_at
        }
    
    def get_rating_distribution(self, book_id: int) -> Dict[int, int]:
        """Get rating distribution for a book."""
        cache_key = f"rating_dist:{book_id}"
        
        # Try cache first
        if self.redis_client:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            except Exception:
                pass
        
        # Query rating distribution
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
        
        # Cache the result
        if self.redis_client:
            try:
                self.redis_client.setex(cache_key, 1800, json.dumps(distribution))  # 30 minutes
            except Exception:
                pass
        
        return distribution
    
    def _update_book_rating_stats(self, book_id: int) -> None:
        """Update book's average rating and review count."""
        # Calculate new stats
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
        
        # Update book
        book = self.db.query(Book).filter(Book.id == book_id).first()
        if book:
            book.average_rating = avg_rating
            book.review_count = review_count
            # Update legacy fields
            book.note_moyenne = avg_rating
            book.nombre_reviews = review_count
            
            self.db.commit()
    
    def _invalidate_review_caches(self, book_id: int) -> None:
        """Invalidate review-related caches."""
        if not self.redis_client:
            return
        
        try:
            # Invalidate rating distribution cache
            self.redis_client.delete(f"rating_dist:{book_id}")
            
            # Invalidate book caches (this will be handled by BookService)
            # We could emit an event here or call BookService directly
            
        except Exception:
            pass
    
    def get_recent_reviews(self, limit: int = 10) -> List[Dict]:
        """Get most recent reviews across all books."""
        reviews = (
            self.db.query(Review)
            .order_by(desc(Review.created_at))
            .limit(limit)
            .all()
        )
        
        reviews_list = []
        for review in reviews:
            user = self.db.query(User).filter(User.id == review.user_id).first()
            book = self.db.query(Book).filter(Book.id == review.book_id).first()
            
            review_dict = {
                "id": review.id,
                "rating": review.rating,
                "title": review.title,
                "content": review.content[:200] + "..." if review.content and len(review.content) > 200 else review.content,
                "created_at": review.created_at,
                "user": {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name
                } if user else None,
                "book": {
                    "id": book.id,
                    "titre": book.titre,
                    "author_names": book.author_names or []
                } if book else None
            }
            reviews_list.append(review_dict)
        
        return reviews_list