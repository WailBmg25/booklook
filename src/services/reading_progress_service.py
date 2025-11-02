"""Reading progress service for tracking user reading sessions."""

from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from models.book import ReadingProgress, Book, User
from datetime import datetime, timedelta


class ReadingProgressService:
    """Service for managing user reading progress and history."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def update_reading_progress(
        self,
        user_id: int,
        book_id: int,
        current_page: int,
        total_pages: Optional[int] = None
    ) -> Optional[Dict]:
        """Update or create reading progress for a user and book."""
        # Verify user and book exist
        user = self.db.query(User).filter(User.id == user_id).first()
        book = self.db.query(Book).filter(Book.id == book_id).first()
        
        if not user or not book:
            return None
        
        # Get or create reading progress
        progress = self.db.query(ReadingProgress).filter(
            and_(ReadingProgress.user_id == user_id, ReadingProgress.book_id == book_id)
        ).first()
        
        if not progress:
            progress = ReadingProgress(
                user_id=user_id,
                book_id=book_id,
                current_page=current_page,
                total_pages=total_pages or book.total_pages or book.nombre_pages,
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
        
        return {
            "user_id": progress.user_id,
            "book_id": progress.book_id,
            "current_page": progress.current_page,
            "total_pages": progress.total_pages,
            "progress_percentage": progress.progress_percentage,
            "last_read_at": progress.last_read_at,
            "created_at": progress.created_at,
            "updated_at": progress.updated_at,
            "book": {
                "id": book.id,
                "titre": book.titre,
                "author_names": book.author_names or [],
                "image_url": book.image_url
            }
        }
    
    def get_reading_progress(self, user_id: int, book_id: int) -> Optional[Dict]:
        """Get reading progress for a specific user and book."""
        progress = self.db.query(ReadingProgress).filter(
            and_(ReadingProgress.user_id == user_id, ReadingProgress.book_id == book_id)
        ).first()
        
        if not progress:
            return None
        
        book = self.db.query(Book).filter(Book.id == book_id).first()
        
        return {
            "user_id": progress.user_id,
            "book_id": progress.book_id,
            "current_page": progress.current_page,
            "total_pages": progress.total_pages,
            "progress_percentage": progress.progress_percentage,
            "last_read_at": progress.last_read_at,
            "created_at": progress.created_at,
            "updated_at": progress.updated_at,
            "book": {
                "id": book.id,
                "titre": book.titre,
                "author_names": book.author_names or [],
                "image_url": book.image_url
            } if book else None
        }
    
    def get_user_reading_history(
        self,
        user_id: int,
        limit: int = 20,
        days_back: int = 30
    ) -> List[Dict]:
        """Get user's recent reading history."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        progress_records = (
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
        
        history = []
        for progress in progress_records:
            book = self.db.query(Book).filter(Book.id == progress.book_id).first()
            
            history_item = {
                "book_id": progress.book_id,
                "current_page": progress.current_page,
                "total_pages": progress.total_pages,
                "progress_percentage": progress.progress_percentage,
                "last_read_at": progress.last_read_at,
                "book": {
                    "id": book.id,
                    "titre": book.titre,
                    "author_names": book.author_names or [],
                    "image_url": book.image_url,
                    "average_rating": float(book.average_rating) if book.average_rating else 0.0
                } if book else None
            }
            history.append(history_item)
        
        return history
    
    def get_currently_reading(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get books the user is currently reading (not finished)."""
        progress_records = (
            self.db.query(ReadingProgress)
            .filter(
                and_(
                    ReadingProgress.user_id == user_id,
                    ReadingProgress.progress_percentage < 100.0
                )
            )
            .order_by(desc(ReadingProgress.last_read_at))
            .limit(limit)
            .all()
        )
        
        currently_reading = []
        for progress in progress_records:
            book = self.db.query(Book).filter(Book.id == progress.book_id).first()
            
            reading_item = {
                "book_id": progress.book_id,
                "current_page": progress.current_page,
                "total_pages": progress.total_pages,
                "progress_percentage": progress.progress_percentage,
                "last_read_at": progress.last_read_at,
                "book": {
                    "id": book.id,
                    "titre": book.titre,
                    "author_names": book.author_names or [],
                    "image_url": book.image_url,
                    "average_rating": float(book.average_rating) if book.average_rating else 0.0
                } if book else None
            }
            currently_reading.append(reading_item)
        
        return currently_reading
    
    def get_finished_books(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get books the user has finished reading."""
        progress_records = (
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
        
        finished_books = []
        for progress in progress_records:
            book = self.db.query(Book).filter(Book.id == progress.book_id).first()
            
            finished_item = {
                "book_id": progress.book_id,
                "current_page": progress.current_page,
                "total_pages": progress.total_pages,
                "progress_percentage": progress.progress_percentage,
                "finished_at": progress.last_read_at,  # When they reached 100%
                "book": {
                    "id": book.id,
                    "titre": book.titre,
                    "author_names": book.author_names or [],
                    "image_url": book.image_url,
                    "average_rating": float(book.average_rating) if book.average_rating else 0.0
                } if book else None
            }
            finished_books.append(finished_item)
        
        return finished_books
    
    def get_reading_stats(self, user_id: int) -> Dict:
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
    
    def delete_reading_progress(self, user_id: int, book_id: int) -> bool:
        """Delete reading progress for a user and book."""
        progress = self.db.query(ReadingProgress).filter(
            and_(ReadingProgress.user_id == user_id, ReadingProgress.book_id == book_id)
        ).first()
        
        if not progress:
            return False
        
        self.db.delete(progress)
        self.db.commit()
        return True
    
    def mark_book_as_finished(self, user_id: int, book_id: int) -> Optional[Dict]:
        """Mark a book as finished (100% progress)."""
        book = self.db.query(Book).filter(Book.id == book_id).first()
        if not book:
            return None
        
        total_pages = book.total_pages or book.nombre_pages or 100
        
        return self.update_reading_progress(
            user_id=user_id,
            book_id=book_id,
            current_page=total_pages,
            total_pages=total_pages
        )
    
    def get_reading_session_info(self, user_id: int, book_id: int) -> Optional[Dict]:
        """Get information needed to resume a reading session."""
        progress = self.get_reading_progress(user_id, book_id)
        if not progress:
            return None
        
        book = self.db.query(Book).filter(Book.id == book_id).first()
        if not book:
            return None
        
        # Calculate suggested reading position based on words per page
        words_per_page = 300  # Default words per page for content pagination
        current_word = (progress["current_page"] - 1) * words_per_page
        
        return {
            "book_id": book_id,
            "current_page": progress["current_page"],
            "total_pages": progress["total_pages"],
            "progress_percentage": progress["progress_percentage"],
            "current_word_position": current_word,
            "last_read_at": progress["last_read_at"],
            "book_info": {
                "id": book.id,
                "titre": book.titre,
                "author_names": book.author_names or [],
                "word_count": book.word_count,
                "content_path": book.content_path
            }
        }