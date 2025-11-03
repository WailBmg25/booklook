"""Reading progress repository for reading progress database operations."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from models import ReadingProgress, Book, User
from .base_repository import BaseRepository
from datetime import datetime, timedelta


class ReadingProgressRepository(BaseRepository[ReadingProgress]):
    """Repository for reading progress data access operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, ReadingProgress)
    
    def get_user_book_progress(self, user_id: int, book_id: int) -> Optional[ReadingProgress]:
        """Get reading progress for a specific user and book."""
        return self.db.query(ReadingProgress).filter(
            and_(ReadingProgress.user_id == user_id, ReadingProgress.book_id == book_id)
        ).first()
    
    def create_or_update_progress(
        self,
        user_id: int,
        book_id: int,
        current_page: int,
        total_pages: Optional[int] = None
    ) -> ReadingProgress:
        """Create or update reading progress."""
        progress = self.get_user_book_progress(user_id, book_id)
        
        if not progress:
            # Get total pages from book if not provided
            if total_pages is None:
                book = self.db.query(Book).filter(Book.id == book_id).first()
                total_pages = book.total_pages or book.nombre_pages if book else None
            
            progress = ReadingProgress(
                user_id=user_id,
                book_id=book_id,
                current_page=current_page,
                total_pages=total_pages,
                last_read_at=datetime.utcnow()
            )
            self.db.add(progress)
        else:
            progress.current_page = current_page
            if total_pages:
                progress.total_pages = total_pages
            progress.last_read_at = datetime.utcnow()
        
        # Calculate progress percentage
        if progress.total_pages and progress.total_pages > 0:
            progress.progress_percentage = min(100.0, (current_page / progress.total_pages) * 100)
        else:
            progress.progress_percentage = 0.0
        
        self.db.commit()
        self.db.refresh(progress)
        return progress
    
    def get_user_reading_history(
        self,
        user_id: int,
        limit: int = 20,
        days_back: int = 30
    ) -> List[ReadingProgress]:
        """Get user's recent reading history."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        return (
            self.db.query(ReadingProgress)
            .filter(
                and_(
                    ReadingProgress.user_id == user_id,
                    ReadingProgress.last_read_at >= cutoff_date
                )
            )
            .order_by(desc(ReadingProgress.last_read_at))
            .limit(limit)
            .all()
        )
    
    def get_currently_reading(self, user_id: int, limit: int = 10) -> List[ReadingProgress]:
        """Get books the user is currently reading (not finished)."""
        return (
            self.db.query(ReadingProgress)
            .filter(
                and_(
                    ReadingProgress.user_id == user_id,
                    ReadingProgress.progress_percentage < 100.0,
                    ReadingProgress.progress_percentage > 0.0
                )
            )
            .order_by(desc(ReadingProgress.last_read_at))
            .limit(limit)
            .all()
        )
    
    def get_finished_books(self, user_id: int, limit: int = 20) -> List[ReadingProgress]:
        """Get books the user has finished reading."""
        return (
            self.db.query(ReadingProgress)
            .filter(
                and_(
                    ReadingProgress.user_id == user_id,
                    ReadingProgress.progress_percentage >= 100.0
                )
            )
            .order_by(desc(ReadingProgress.last_read_at))
            .limit(limit)
            .all()
        )
    
    def get_user_reading_stats(self, user_id: int) -> Dict[str, Any]:
        """Get reading statistics for a user."""
        # Total books started
        total_started = (
            self.db.query(ReadingProgress)
            .filter(ReadingProgress.user_id == user_id)
            .count()
        )
        
        # Books finished
        books_finished = (
            self.db.query(ReadingProgress)
            .filter(
                and_(
                    ReadingProgress.user_id == user_id,
                    ReadingProgress.progress_percentage >= 100.0
                )
            )
            .count()
        )
        
        # Currently reading
        currently_reading = (
            self.db.query(ReadingProgress)
            .filter(
                and_(
                    ReadingProgress.user_id == user_id,
                    ReadingProgress.progress_percentage < 100.0,
                    ReadingProgress.progress_percentage > 0.0
                )
            )
            .count()
        )
        
        # Average progress
        avg_progress_result = (
            self.db.query(func.avg(ReadingProgress.progress_percentage))
            .filter(ReadingProgress.user_id == user_id)
            .scalar()
        )
        avg_progress = float(avg_progress_result) if avg_progress_result else 0.0
        
        # Reading activity in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_activity = (
            self.db.query(ReadingProgress)
            .filter(
                and_(
                    ReadingProgress.user_id == user_id,
                    ReadingProgress.last_read_at >= thirty_days_ago
                )
            )
            .count()
        )
        
        return {
            "total_books_started": total_started,
            "books_finished": books_finished,
            "currently_reading": currently_reading,
            "average_progress": round(avg_progress, 2),
            "recent_activity_count": recent_activity,
            "completion_rate": round((books_finished / total_started * 100), 2) if total_started > 0 else 0.0
        }
    
    def delete_progress(self, user_id: int, book_id: int) -> bool:
        """Delete reading progress for a user and book."""
        progress = self.get_user_book_progress(user_id, book_id)
        if not progress:
            return False
        
        self.db.delete(progress)
        self.db.commit()
        return True
    
    def mark_book_as_finished(self, user_id: int, book_id: int) -> Optional[ReadingProgress]:
        """Mark a book as finished (100% progress)."""
        book = self.db.query(Book).filter(Book.id == book_id).first()
        if not book:
            return None
        
        total_pages = book.total_pages or book.nombre_pages or 100
        
        return self.create_or_update_progress(
            user_id=user_id,
            book_id=book_id,
            current_page=total_pages,
            total_pages=total_pages
        )
    
    def get_progress_with_book_info(self, user_id: int, book_id: int) -> Optional[Dict[str, Any]]:
        """Get reading progress with book information."""
        progress = self.get_user_book_progress(user_id, book_id)
        if not progress:
            return None
        
        book = self.db.query(Book).filter(Book.id == book_id).first()
        
        return {
            "progress": progress,
            "book": book
        }
    
    def get_all_user_progress(self, user_id: int) -> List[ReadingProgress]:
        """Get all reading progress for a user."""
        return (
            self.db.query(ReadingProgress)
            .filter(ReadingProgress.user_id == user_id)
            .order_by(desc(ReadingProgress.last_read_at))
            .all()
        )
    
    def get_book_readers_count(self, book_id: int) -> int:
        """Get count of users who have started reading a book."""
        return (
            self.db.query(ReadingProgress)
            .filter(ReadingProgress.book_id == book_id)
            .count()
        )
    
    def get_book_completion_stats(self, book_id: int) -> Dict[str, Any]:
        """Get completion statistics for a book."""
        total_readers = self.get_book_readers_count(book_id)
        
        finished_readers = (
            self.db.query(ReadingProgress)
            .filter(
                and_(
                    ReadingProgress.book_id == book_id,
                    ReadingProgress.progress_percentage >= 100.0
                )
            )
            .count()
        )
        
        avg_progress_result = (
            self.db.query(func.avg(ReadingProgress.progress_percentage))
            .filter(ReadingProgress.book_id == book_id)
            .scalar()
        )
        avg_progress = float(avg_progress_result) if avg_progress_result else 0.0
        
        return {
            "total_readers": total_readers,
            "finished_readers": finished_readers,
            "completion_rate": round((finished_readers / total_readers * 100), 2) if total_readers > 0 else 0.0,
            "average_progress": round(avg_progress, 2)
        }
    
    def delete_all_user_progress(self, user_id: int) -> int:
        """Delete all reading progress for a user (admin operation)."""
        count = self.db.query(ReadingProgress).filter(ReadingProgress.user_id == user_id).count()
        self.db.query(ReadingProgress).filter(ReadingProgress.user_id == user_id).delete()
        self.db.commit()
        return count
    
    def delete_all_book_progress(self, book_id: int) -> int:
        """Delete all reading progress for a book (admin operation)."""
        count = self.db.query(ReadingProgress).filter(ReadingProgress.book_id == book_id).count()
        self.db.query(ReadingProgress).filter(ReadingProgress.book_id == book_id).delete()
        self.db.commit()
        return count