"""Reading progress controller for reading progress business logic."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from repositories import ReadingProgressRepository, BookRepository
from models import ReadingProgress
from helpers import ValidationHelper
from datetime import datetime


class ReadingProgressController:
    """Controller for reading progress business logic operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.progress_repo = ReadingProgressRepository(db)
        self.book_repo = BookRepository(db)
    
    def update_reading_progress(
        self,
        user_id: int,
        book_id: int,
        current_page: int,
        total_pages: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Update or create reading progress with business logic."""
        # Validate reading progress data
        validation_result = ValidationHelper.validate_reading_progress(current_page, total_pages)
        if not validation_result["is_valid"]:
            return {"error": "Invalid reading progress data", "issues": validation_result["issues"]}
        
        # Create or update progress using repository
        progress = self.progress_repo.create_or_update_progress(
            user_id=user_id,
            book_id=book_id,
            current_page=current_page,
            total_pages=total_pages
        )
        
        # Get progress with book info
        progress_data = self.progress_repo.get_progress_with_book_info(user_id, book_id)
        if not progress_data:
            return None
        
        # Use model business logic for response
        return progress_data["progress"].to_dict(include_book=True)
    
    def get_reading_progress(self, user_id: int, book_id: int) -> Optional[Dict[str, Any]]:
        """Get reading progress for a specific user and book."""
        progress_data = self.progress_repo.get_progress_with_book_info(user_id, book_id)
        if not progress_data:
            return None
        
        # Use model business logic for response
        return progress_data["progress"].to_dict(include_book=True)
    
    def get_user_reading_history(
        self,
        user_id: int,
        limit: int = 20,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """Get user's recent reading history."""
        progress_records = self.progress_repo.get_user_reading_history(user_id, limit, days_back)
        
        # Convert using model business logic
        history = []
        for progress in progress_records:
            progress_data = self.progress_repo.get_progress_with_book_info(user_id, progress.book_id)
            if progress_data:
                history.append(progress_data["progress"].to_dict(include_book=True))
        
        return history
    
    def get_currently_reading(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get books the user is currently reading."""
        progress_records = self.progress_repo.get_currently_reading(user_id, limit)
        
        # Convert using model business logic
        currently_reading = []
        for progress in progress_records:
            progress_data = self.progress_repo.get_progress_with_book_info(user_id, progress.book_id)
            if progress_data:
                currently_reading.append(progress_data["progress"].to_dict(include_book=True))
        
        return currently_reading
    
    def get_finished_books(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Get books the user has finished reading."""
        progress_records = self.progress_repo.get_finished_books(user_id, limit)
        
        # Convert using model business logic
        finished_books = []
        for progress in progress_records:
            progress_data = self.progress_repo.get_progress_with_book_info(user_id, progress.book_id)
            if progress_data:
                finished_item = progress_data["progress"].to_dict(include_book=True)
                finished_item["finished_at"] = progress.last_read_at  # When they reached 100%
                finished_books.append(finished_item)
        
        return finished_books
    
    def get_reading_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive reading statistics for a user."""
        # Get basic stats from repository
        stats = self.progress_repo.get_user_reading_stats(user_id)
        
        # Add business logic enhancements
        enhanced_stats = {
            **stats,
            "reading_level": self._calculate_reading_level(stats),
            "reading_consistency": self._calculate_reading_consistency(user_id),
            "favorite_genres": self._get_user_favorite_genres(user_id)
        }
        
        return enhanced_stats
    
    def mark_book_as_finished(self, user_id: int, book_id: int) -> Optional[Dict[str, Any]]:
        """Mark a book as finished using business logic."""
        progress = self.progress_repo.mark_book_as_finished(user_id, book_id)
        if not progress:
            return None
        
        # Get progress with book info
        progress_data = self.progress_repo.get_progress_with_book_info(user_id, book_id)
        if not progress_data:
            return None
        
        return progress_data["progress"].to_dict(include_book=True)
    
    def delete_reading_progress(self, user_id: int, book_id: int) -> bool:
        """Delete reading progress for a user and book."""
        return self.progress_repo.delete_progress(user_id, book_id)
    
    def get_reading_session_info(self, user_id: int, book_id: int) -> Optional[Dict[str, Any]]:
        """Get information needed to resume a reading session."""
        progress_data = self.progress_repo.get_progress_with_book_info(user_id, book_id)
        if not progress_data:
            return None
        
        progress = progress_data["progress"]
        book = progress_data["book"]
        
        # Calculate suggested reading position based on words per page
        words_per_page = 300  # Default words per page for content pagination
        current_word = (progress.current_page - 1) * words_per_page
        
        # Use model business logic for calculations
        estimated_time_remaining = progress.get_estimated_time_remaining()
        
        return {
            "book_id": book_id,
            "book_title": book.get_display_title() if book else "Unknown",
            "current_page": progress.current_page,
            "total_pages": progress.total_pages,
            "progress_percentage": progress.progress_percentage,
            "current_word_position": current_word,
            "last_read_at": progress.last_read_at,
            "estimated_time_remaining": estimated_time_remaining,
            "reading_status": progress.get_progress_status(),
            "pages_remaining": progress.get_pages_remaining(),
            "book_info": {
                "id": book.id,
                "titre": book.titre,
                "author_names": book.author_names or [],
                "word_count": book.word_count,
                "content_path": book.content_path
            } if book else None
        }
    
    def get_book_completion_stats(self, book_id: int) -> Dict[str, Any]:
        """Get completion statistics for a book."""
        return self.progress_repo.get_book_completion_stats(book_id)
    
    def calculate_reading_speed(self, user_id: int, book_id: int) -> Optional[Dict[str, Any]]:
        """Calculate user's reading speed for a book."""
        progress = self.progress_repo.get_user_book_progress(user_id, book_id)
        if not progress:
            return None
        
        book = self.book_repo.get_by_id(book_id)
        if not book or not book.word_count:
            return None
        
        # Calculate reading speed based on progress and time
        if progress.created_at and progress.last_read_at:
            time_spent = (progress.last_read_at - progress.created_at).total_seconds() / 60  # minutes
            if time_spent > 0:
                words_read = (progress.progress_percentage / 100) * book.word_count
                words_per_minute = words_read / time_spent
                
                return {
                    "words_per_minute": round(words_per_minute, 2),
                    "time_spent_minutes": round(time_spent, 2),
                    "words_read": round(words_read),
                    "reading_level": self._classify_reading_speed(words_per_minute)
                }
        
        return None
    
    def get_reading_streaks(self, user_id: int) -> Dict[str, Any]:
        """Get reading streak information for a user."""
        all_progress = self.progress_repo.get_all_user_progress(user_id)
        
        if not all_progress:
            return {"current_streak": 0, "longest_streak": 0, "total_reading_days": 0}
        
        # Sort by last read date
        sorted_progress = sorted(all_progress, key=lambda p: p.last_read_at or datetime.min, reverse=True)
        
        current_streak = 0
        longest_streak = 0
        temp_streak = 0
        
        # Calculate streaks using model business logic
        for progress in sorted_progress:
            if progress.is_recently_read(1):  # Read within last day
                temp_streak += 1
                if temp_streak > longest_streak:
                    longest_streak = temp_streak
                if current_streak == 0:  # First recent read
                    current_streak = temp_streak
            else:
                temp_streak = 0
        
        total_reading_days = len([p for p in all_progress if p.is_recently_read(365)])  # Last year
        
        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "total_reading_days": total_reading_days
        }
    
    def _calculate_reading_level(self, stats: Dict[str, Any]) -> str:
        """Calculate user's reading level based on statistics."""
        completion_rate = stats.get("completion_rate", 0)
        books_finished = stats.get("books_finished", 0)
        
        if completion_rate >= 80 and books_finished >= 20:
            return "Expert"
        elif completion_rate >= 60 and books_finished >= 10:
            return "Advanced"
        elif completion_rate >= 40 and books_finished >= 5:
            return "Intermediate"
        else:
            return "Beginner"
    
    def _calculate_reading_consistency(self, user_id: int) -> str:
        """Calculate reading consistency based on recent activity."""
        recent_progress = self.progress_repo.get_user_reading_history(user_id, limit=50, days_back=30)
        
        if len(recent_progress) >= 20:
            return "Very Consistent"
        elif len(recent_progress) >= 10:
            return "Consistent"
        elif len(recent_progress) >= 5:
            return "Moderate"
        else:
            return "Inconsistent"
    
    def _get_user_favorite_genres(self, user_id: int) -> List[str]:
        """Get user's favorite genres based on reading history."""
        all_progress = self.progress_repo.get_all_user_progress(user_id)
        genre_counts = {}
        
        for progress in all_progress:
            book = self.book_repo.get_by_id(progress.book_id)
            if book and book.genre_names:
                for genre in book.genre_names:
                    genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        # Return top 3 genres
        sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
        return [genre for genre, count in sorted_genres[:3]]
    
    def _classify_reading_speed(self, words_per_minute: float) -> str:
        """Classify reading speed."""
        if words_per_minute >= 300:
            return "Fast"
        elif words_per_minute >= 200:
            return "Average"
        else:
            return "Slow"