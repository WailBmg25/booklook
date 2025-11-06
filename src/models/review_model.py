"""Review model with business logic methods."""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey('books.id', ondelete='CASCADE'), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=True)
    is_flagged = Column(Integer, default=False, nullable=False)  # For moderation
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Legacy fields for backward compatibility
    livre_id = Column(Integer, ForeignKey('books.id', ondelete='CASCADE'), nullable=True, index=True)
    note = Column(Integer, nullable=True)  # Maps to rating
    commentaire = Column(Text, nullable=True)  # Maps to content
    nom_utilisateur = Column(String(100), nullable=True)  # For anonymous reviews

    # Relations
    book = relationship("Book", back_populates="reviews", foreign_keys=[book_id])
    user = relationship("User", back_populates="reviews")
    
    # Legacy relationship for backward compatibility
    livre = relationship("Book", foreign_keys=[livre_id], viewonly=True)

    def __repr__(self):
        return f"<Review(id={self.id}, book_id={self.book_id}, rating={self.rating})>"
    
    # Business Logic Methods
    def is_valid_rating(self) -> bool:
        """Check if rating is within valid range."""
        return 1 <= self.rating <= 5
    
    def get_rating_stars(self) -> str:
        """Get rating as star representation."""
        return "★" * self.rating + "☆" * (5 - self.rating)
    
    def is_positive_review(self) -> bool:
        """Check if review is positive (4-5 stars)."""
        return self.rating >= 4
    
    def is_negative_review(self) -> bool:
        """Check if review is negative (1-2 stars)."""
        return self.rating <= 2
    
    def is_neutral_review(self) -> bool:
        """Check if review is neutral (3 stars)."""
        return self.rating == 3
    
    def has_content(self) -> bool:
        """Check if review has written content."""
        return bool(self.content and self.content.strip())
    
    def has_title(self) -> bool:
        """Check if review has a title."""
        return bool(self.title and self.title.strip())
    
    def get_content_preview(self, max_length: int = 150) -> str:
        """Get truncated content for preview."""
        if not self.content:
            return ""
        
        if len(self.content) <= max_length:
            return self.content
        
        return self.content[:max_length].rsplit(' ', 1)[0] + "..."
    
    def get_display_title(self) -> str:
        """Get display title or generate one from rating."""
        if self.title:
            return self.title
        
        rating_titles = {
            5: "Excellent!",
            4: "Very Good",
            3: "Good",
            2: "Fair",
            1: "Poor"
        }
        
        return rating_titles.get(self.rating, "Review")
    
    def is_recent(self, days: int = 7) -> bool:
        """Check if review was created recently."""
        from datetime import datetime, timedelta
        if not self.created_at:
            return False
        
        from datetime import timezone
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        # Make created_at timezone-aware if it isn't
        created_at = self.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        return created_at >= cutoff_date
    
    def get_sentiment(self) -> str:
        """Get review sentiment based on rating."""
        if self.is_positive_review():
            return "positive"
        elif self.is_negative_review():
            return "negative"
        else:
            return "neutral"
    
    def get_word_count(self) -> int:
        """Get word count of review content."""
        if not self.content:
            return 0
        return len(self.content.split())
    
    def is_detailed_review(self, min_words: int = 50) -> bool:
        """Check if review is detailed (has sufficient content)."""
        return self.get_word_count() >= min_words
    
    def update_legacy_fields(self) -> None:
        """Update legacy fields for backward compatibility."""
        self.livre_id = self.book_id
        self.note = self.rating
        self.commentaire = self.content
    
    def to_dict(self, include_user: bool = True, include_book: bool = False) -> dict:
        """Convert review to dictionary for API responses."""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "book_id": self.book_id,
            "rating": self.rating,
            "title": self.title,
            "content": self.content,
            "content_preview": self.get_content_preview(),
            "rating_stars": self.get_rating_stars(),
            "display_title": self.get_display_title(),
            "is_positive": self.is_positive_review(),
            "is_negative": self.is_negative_review(),
            "is_neutral": self.is_neutral_review(),
            "sentiment": self.get_sentiment(),
            "word_count": self.get_word_count(),
            "is_detailed": self.is_detailed_review(),
            "is_recent": self.is_recent(),
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
        if include_user and hasattr(self, 'user') and self.user:
            data["user"] = self.user.to_public_dict()
        
        if include_book and hasattr(self, 'book') and self.book:
            data["book"] = {
                "id": self.book.id,
                "titre": self.book.titre,
                "author_names": self.book.author_names or []
            }
        
        return data