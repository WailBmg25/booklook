"""User model with business logic methods."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from .associations import user_favorite_association


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Legacy fields for backward compatibility
    nom = Column(String(100), nullable=True)  # Maps to last_name
    prenom = Column(String(100), nullable=True)  # Maps to first_name
    photo_url = Column(String(500), nullable=True)

    # Relations
    livres_favoris = relationship("Book", secondary=user_favorite_association, back_populates="favoris_par")
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    reading_progress = relationship("ReadingProgress", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
    
    # Business Logic Methods
    def get_full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_display_name(self) -> str:
        """Get user's display name (first name or full name)."""
        return self.first_name or self.get_full_name() or self.email.split('@')[0]
    
    def is_book_favorited(self, book_id: int) -> bool:
        """Check if a book is in user's favorites."""
        return any(book.id == book_id for book in self.livres_favoris)
    
    def add_favorite_book(self, book) -> bool:
        """Add book to favorites if not already added."""
        if not self.is_book_favorited(book.id):
            self.livres_favoris.append(book)
            return True
        return False
    
    def remove_favorite_book(self, book) -> bool:
        """Remove book from favorites if it exists."""
        if self.is_book_favorited(book.id):
            self.livres_favoris.remove(book)
            return True
        return False
    
    def get_favorites_count(self) -> int:
        """Get count of favorite books."""
        return len(self.livres_favoris)
    
    def get_reviews_count(self) -> int:
        """Get count of reviews written by user."""
        return len(self.reviews)
    
    def has_reviewed_book(self, book_id: int) -> bool:
        """Check if user has reviewed a specific book."""
        return any(review.book_id == book_id for review in self.reviews)
    
    def get_average_rating_given(self) -> float:
        """Get average rating given by user in their reviews."""
        if not self.reviews:
            return 0.0
        
        total_rating = sum(review.rating for review in self.reviews)
        return total_rating / len(self.reviews)
    
    def is_active_reviewer(self, min_reviews: int = 3) -> bool:
        """Check if user is an active reviewer."""
        return self.get_reviews_count() >= min_reviews
    
    def get_reading_progress_count(self) -> int:
        """Get count of books with reading progress."""
        return len(self.reading_progress)
    
    def get_finished_books_count(self) -> int:
        """Get count of finished books."""
        return len([p for p in self.reading_progress if p.progress_percentage >= 100.0])
    
    def get_completion_rate(self) -> float:
        """Get reading completion rate."""
        total_started = self.get_reading_progress_count()
        if total_started == 0:
            return 0.0
        
        finished = self.get_finished_books_count()
        return (finished / total_started) * 100
    
    def update_legacy_fields(self) -> None:
        """Update legacy fields for backward compatibility."""
        self.nom = self.last_name
        self.prenom = self.first_name
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert user to dictionary for API responses."""
        data = {
            "id": self.id,
            "email": self.email if include_sensitive else None,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.get_full_name(),
            "display_name": self.get_display_name(),
            "is_active": self.is_active,
            "photo_url": self.photo_url,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "favorites_count": self.get_favorites_count(),
            "reviews_count": self.get_reviews_count(),
            "reading_progress_count": self.get_reading_progress_count(),
            "finished_books_count": self.get_finished_books_count(),
            "completion_rate": self.get_completion_rate(),
            "average_rating_given": self.get_average_rating_given(),
            "is_active_reviewer": self.is_active_reviewer()
        }
        
        # Remove None values
        return {k: v for k, v in data.items() if v is not None}
    
    def to_public_dict(self) -> dict:
        """Convert user to public dictionary (no sensitive info)."""
        return self.to_dict(include_sensitive=False)