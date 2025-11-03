"""Reading progress model with business logic methods."""

from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class ReadingProgress(Base):
    __tablename__ = "reading_progress"

    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    book_id = Column(Integer, ForeignKey('books.id', ondelete='CASCADE'), primary_key=True)
    current_page = Column(Integer, default=1)
    total_pages = Column(Integer, nullable=True)
    progress_percentage = Column(Float, default=0.0)  # 0.0 to 100.0
    last_read_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations
    user = relationship("User", back_populates="reading_progress")
    book = relationship("Book")

    def __repr__(self):
        return f"<ReadingProgress(user_id={self.user_id}, book_id={self.book_id}, page={self.current_page})>"
    
    # Business Logic Methods
    def calculate_progress_percentage(self) -> float:
        """Calculate and update progress percentage."""
        if not self.total_pages or self.total_pages <= 0:
            return 0.0
        
        percentage = min(100.0, (self.current_page / self.total_pages) * 100)
        self.progress_percentage = percentage
        return percentage
    
    def is_finished(self) -> bool:
        """Check if book is finished (100% progress)."""
        return (self.progress_percentage or 0.0) >= 100.0
    
    def is_started(self) -> bool:
        """Check if book reading has started."""
        return (self.progress_percentage or 0.0) > 0.0
    
    def is_in_progress(self) -> bool:
        """Check if book is currently being read."""
        progress = self.progress_percentage or 0.0
        return 0.0 < progress < 100.0
    
    def is_not_started(self) -> bool:
        """Check if book reading hasn't started."""
        return (self.progress_percentage or 0.0) == 0.0
    
    def get_pages_remaining(self) -> int:
        """Get number of pages remaining."""
        if not self.total_pages:
            return 0
        return max(0, self.total_pages - self.current_page)
    
    def get_pages_read(self) -> int:
        """Get number of pages read."""
        return max(0, self.current_page - 1)  # Assuming page 1 is the start
    
    def get_progress_status(self) -> str:
        """Get human-readable progress status."""
        if self.is_finished():
            return "Finished"
        elif self.is_in_progress():
            return "In Progress"
        elif self.is_started():
            return "Started"
        else:
            return "Not Started"
    
    def get_progress_category(self) -> str:
        """Get progress category for analytics."""
        if self.progress_percentage >= 100:
            return "completed"
        elif self.progress_percentage >= 75:
            return "nearly_finished"
        elif self.progress_percentage >= 50:
            return "halfway"
        elif self.progress_percentage >= 25:
            return "quarter_way"
        elif self.progress_percentage > 0:
            return "just_started"
        else:
            return "not_started"
    
    def get_estimated_time_remaining(self, words_per_minute: int = 200) -> int:
        """Get estimated reading time remaining in minutes."""
        if not hasattr(self, 'book') or not self.book or not self.book.word_count:
            return 0
        
        if self.is_finished():
            return 0
        
        words_per_page = self.book.word_count / (self.total_pages or 1)
        remaining_words = self.get_pages_remaining() * words_per_page
        
        return int(remaining_words / words_per_minute)
    
    def update_reading_position(self, current_page: int) -> None:
        """Update current reading position and recalculate progress."""
        from datetime import datetime
        
        self.current_page = current_page
        self.last_read_at = datetime.utcnow()
        self.calculate_progress_percentage()
    
    def mark_as_finished(self) -> None:
        """Mark book as finished."""
        from datetime import datetime
        
        if self.total_pages:
            self.current_page = self.total_pages
        self.progress_percentage = 100.0
        self.last_read_at = datetime.utcnow()
    
    def reset_progress(self) -> None:
        """Reset reading progress to beginning."""
        from datetime import datetime
        
        self.current_page = 1
        self.progress_percentage = 0.0
        self.last_read_at = datetime.utcnow()
    
    def is_recently_read(self, days: int = 7) -> bool:
        """Check if book was read recently."""
        from datetime import datetime, timedelta, timezone
        
        if not self.last_read_at:
            return False
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        # Make last_read_at timezone-aware if it isn't
        last_read_at = self.last_read_at
        if last_read_at.tzinfo is None:
            last_read_at = last_read_at.replace(tzinfo=timezone.utc)
        return last_read_at >= cutoff_date
    
    def get_reading_streak_days(self) -> int:
        """Get number of days since last read (for streak calculation)."""
        from datetime import datetime, timezone
        
        if not self.last_read_at:
            return 0
        
        now = datetime.now(timezone.utc)
        last_read_at = self.last_read_at
        if last_read_at.tzinfo is None:
            last_read_at = last_read_at.replace(tzinfo=timezone.utc)
        days_since = (now - last_read_at).days
        return max(0, days_since)
    
    def get_reading_velocity(self) -> float:
        """Get reading velocity (pages per day) if possible."""
        if not self.created_at or not self.last_read_at:
            return 0.0
        
        days_reading = (self.last_read_at - self.created_at).days
        if days_reading <= 0:
            return 0.0
        
        pages_read = self.get_pages_read()
        return pages_read / days_reading
    
    def to_dict(self, include_book: bool = True) -> dict:
        """Convert reading progress to dictionary for API responses."""
        data = {
            "user_id": self.user_id,
            "book_id": self.book_id,
            "current_page": self.current_page,
            "total_pages": self.total_pages,
            "progress_percentage": self.progress_percentage,
            "pages_remaining": self.get_pages_remaining(),
            "pages_read": self.get_pages_read(),
            "status": self.get_progress_status(),
            "category": self.get_progress_category(),
            "is_finished": self.is_finished(),
            "is_in_progress": self.is_in_progress(),
            "is_recently_read": self.is_recently_read(),
            "reading_velocity": self.get_reading_velocity(),
            "estimated_time_remaining": self.get_estimated_time_remaining(),
            "last_read_at": self.last_read_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
        if include_book and hasattr(self, 'book') and self.book:
            data["book"] = {
                "id": self.book.id,
                "titre": self.book.titre,
                "author_names": self.book.author_names or [],
                "image_url": self.book.image_url,
                "average_rating": float(self.book.average_rating) if self.book.average_rating else 0.0
            }
        
        return data