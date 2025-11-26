"""Book page model for storing book content in database."""

from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class BookPage(Base):
    __tablename__ = "book_pages"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey('books.id', ondelete='CASCADE'), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    word_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    book = relationship("Book", back_populates="pages")

    def __repr__(self):
        return f"<BookPage(book_id={self.book_id}, page={self.page_number}, words={self.word_count})>"
    
    # Business Logic Methods
    def get_content_preview(self, max_length: int = 200) -> str:
        """Get truncated content for preview."""
        if not self.content:
            return ""
        
        if len(self.content) <= max_length:
            return self.content
        
        return self.content[:max_length].rsplit(' ', 1)[0] + "..."
    
    def calculate_word_count(self) -> int:
        """Calculate and update word count from content."""
        if not self.content:
            return 0
        
        self.word_count = len(self.content.split())
        return self.word_count
    
    def has_content(self) -> bool:
        """Check if page has content."""
        return bool(self.content and self.content.strip())
    
    def get_character_count(self) -> int:
        """Get character count of page content."""
        return len(self.content) if self.content else 0
    
    def get_estimated_reading_time(self, words_per_minute: int = 200) -> float:
        """Get estimated reading time in minutes for this page."""
        if not self.word_count:
            return 0.0
        return self.word_count / words_per_minute
    
    def to_dict(self) -> dict:
        """Convert page to dictionary for API responses."""
        return {
            "id": self.id,
            "book_id": self.book_id,
            "page_number": self.page_number,
            "content": self.content,
            "word_count": self.word_count,
            "character_count": self.get_character_count(),
            "estimated_reading_time": self.get_estimated_reading_time(),
            "created_at": self.created_at
        }
    
    def to_dict_without_content(self) -> dict:
        """Convert page to dictionary without full content (for listings)."""
        return {
            "id": self.id,
            "book_id": self.book_id,
            "page_number": self.page_number,
            "content_preview": self.get_content_preview(),
            "word_count": self.word_count,
            "character_count": self.get_character_count(),
            "created_at": self.created_at
        }
