"""Admin analytics controller for system statistics and logging."""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from models import Book, User, Review, ReadingProgress
from controllers.base_controller import BaseController
from datetime import datetime, timedelta


class AdminAnalyticsController(BaseController):
    """Controller for admin analytics and system statistics."""
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    def get_overview_analytics(self) -> Dict[str, Any]:
        """Get overview analytics with key system metrics."""
        # Total counts
        total_books = self.db.query(func.count(Book.id)).scalar() or 0
        total_users = self.db.query(func.count(User.id)).scalar() or 0
        total_reviews = self.db.query(func.count(Review.id)).scalar() or 0
        total_active_users = self.db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
        total_admins = self.db.query(func.count(User.id)).filter(User.is_admin == True).scalar() or 0
        
        # Recent activity (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        new_users_week = self.db.query(func.count(User.id)).filter(User.created_at >= seven_days_ago).scalar() or 0
        new_reviews_week = self.db.query(func.count(Review.id)).filter(Review.created_at >= seven_days_ago).scalar() or 0
        
        # Average ratings
        avg_book_rating = self.db.query(func.avg(Book.average_rating)).scalar() or 0.0
        avg_review_rating = self.db.query(func.avg(Review.rating)).scalar() or 0.0
        
        # Reading progress stats
        total_reading_sessions = self.db.query(func.count(ReadingProgress.user_id)).scalar() or 0
        active_readers = self.db.query(func.count(func.distinct(ReadingProgress.user_id))).scalar() or 0
        
        return {
            "total_books": total_books,
            "total_users": total_users,
            "total_active_users": total_active_users,
            "total_admins": total_admins,
            "total_reviews": total_reviews,
            "total_reading_sessions": total_reading_sessions,
            "active_readers": active_readers,
            "new_users_this_week": new_users_week,
            "new_reviews_this_week": new_reviews_week,
            "average_book_rating": round(float(avg_book_rating), 2),
            "average_review_rating": round(float(avg_review_rating), 2),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def get_user_analytics(self) -> Dict[str, Any]:
        """Get user activity analytics."""
        # User growth by month (last 6 months)
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        user_growth = (
            self.db.query(
                func.date_trunc('month', User.created_at).label('month'),
                func.count(User.id).label('count')
            )
            .filter(User.created_at >= six_months_ago)
            .group_by('month')
            .order_by('month')
            .all()
        )
        
        # Most active users (by review count)
        most_active_reviewers = (
            self.db.query(
                User.id,
                User.email,
                User.first_name,
                User.last_name,
                func.count(Review.id).label('review_count')
            )
            .join(Review, User.id == Review.user_id)
            .group_by(User.id)
            .order_by(desc('review_count'))
            .limit(10)
            .all()
        )
        
        # User status distribution
        active_users = self.db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
        inactive_users = self.db.query(func.count(User.id)).filter(User.is_active == False).scalar() or 0
        
        return {
            "user_growth": [
                {
                    "month": row.month.isoformat() if row.month else None,
                    "count": row.count
                }
                for row in user_growth
            ],
            "most_active_reviewers": [
                {
                    "user_id": row.id,
                    "email": row.email,
                    "name": f"{row.first_name} {row.last_name}",
                    "review_count": row.review_count
                }
                for row in most_active_reviewers
            ],
            "active_users": active_users,
            "inactive_users": inactive_users,
            "total_users": active_users + inactive_users
        }
    
    def get_book_analytics(self) -> Dict[str, Any]:
        """Get book popularity and statistics."""
        # Most popular books (by review count)
        most_reviewed_books = (
            self.db.query(Book)
            .order_by(desc(Book.review_count))
            .limit(10)
            .all()
        )
        
        # Highest rated books (with minimum reviews)
        highest_rated_books = (
            self.db.query(Book)
            .filter(Book.review_count >= 5)
            .order_by(desc(Book.average_rating))
            .limit(10)
            .all()
        )
        
        # Genre distribution
        genre_stats = {}
        books = self.db.query(Book).all()
        for book in books:
            if book.genre_names:
                for genre in book.genre_names:
                    genre_stats[genre] = genre_stats.get(genre, 0) + 1
        
        # Sort genres by count
        top_genres = sorted(genre_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Books without reviews
        books_without_reviews = self.db.query(func.count(Book.id)).filter(Book.review_count == 0).scalar() or 0
        
        return {
            "most_reviewed_books": [
                {
                    "id": book.id,
                    "title": book.titre,
                    "review_count": book.review_count,
                    "average_rating": float(book.average_rating) if book.average_rating else 0.0
                }
                for book in most_reviewed_books
            ],
            "highest_rated_books": [
                {
                    "id": book.id,
                    "title": book.titre,
                    "average_rating": float(book.average_rating) if book.average_rating else 0.0,
                    "review_count": book.review_count
                }
                for book in highest_rated_books
            ],
            "top_genres": [
                {"genre": genre, "count": count}
                for genre, count in top_genres
            ],
            "books_without_reviews": books_without_reviews
        }
    
    def get_review_analytics(self) -> Dict[str, Any]:
        """Get review statistics and trends."""
        # Rating distribution
        rating_distribution = (
            self.db.query(
                Review.rating,
                func.count(Review.id).label('count')
            )
            .group_by(Review.rating)
            .order_by(Review.rating)
            .all()
        )
        
        # Reviews by month (last 6 months)
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        review_trends = (
            self.db.query(
                func.date_trunc('month', Review.created_at).label('month'),
                func.count(Review.id).label('count')
            )
            .filter(Review.created_at >= six_months_ago)
            .group_by('month')
            .order_by('month')
            .all()
        )
        
        # Flagged reviews count
        flagged_reviews = self.db.query(func.count(Review.id)).filter(Review.is_flagged == True).scalar() or 0
        
        return {
            "rating_distribution": [
                {"rating": row.rating, "count": row.count}
                for row in rating_distribution
            ],
            "review_trends": [
                {
                    "month": row.month.isoformat() if row.month else None,
                    "count": row.count
                }
                for row in review_trends
            ],
            "flagged_reviews": flagged_reviews
        }
    
    def get_admin_logs(
        self,
        page: int = 1,
        page_size: int = 50,
        action_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get admin action logs (placeholder for future implementation)."""
        # This is a placeholder for future admin logging functionality
        # In a production system, you would have an AdminLog model to track actions
        
        return {
            "logs": [],
            "total_count": 0,
            "total_pages": 0,
            "current_page": page,
            "page_size": page_size,
            "has_next": False,
            "has_previous": False,
            "message": "Admin logging not yet implemented"
        }
