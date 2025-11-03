"""Genre model with business logic methods."""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from .associations import book_genre_association


class Genre(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    livres = relationship("Book", secondary=book_genre_association, back_populates="genres")

    def __repr__(self):
        return f"<Genre(id={self.id}, nom='{self.nom}')>"
    
    # Business Logic Methods
    def get_display_name(self) -> str:
        """Get genre's display name."""
        return self.nom.title() if self.nom else "Unknown Genre"
    
    def get_books_count(self) -> int:
        """Get count of books in this genre."""
        return len(self.livres)
    
    def is_popular_genre(self, min_books: int = 10) -> bool:
        """Check if genre is popular (has many books)."""
        return self.get_books_count() >= min_books
    
    def has_description(self) -> bool:
        """Check if genre has a description."""
        return bool(self.description and self.description.strip())
    
    def get_description_preview(self, max_length: int = 150) -> str:
        """Get truncated description for preview."""
        if not self.description:
            return ""
        
        if len(self.description) <= max_length:
            return self.description
        
        return self.description[:max_length].rsplit(' ', 1)[0] + "..."
    
    def get_average_rating(self) -> float:
        """Get average rating of books in this genre."""
        if not self.livres:
            return 0.0
        
        total_rating = sum(book.average_rating or 0 for book in self.livres)
        return total_rating / len(self.livres)
    
    def get_top_rated_books(self, limit: int = 5):
        """Get top rated books in this genre."""
        return sorted(
            [book for book in self.livres if book.average_rating],
            key=lambda b: b.average_rating,
            reverse=True
        )[:limit]
    
    def to_dict(self) -> dict:
        """Convert genre to dictionary for API responses."""
        return {
            "id": self.id,
            "nom": self.nom,
            "display_name": self.get_display_name(),
            "description": self.description,
            "description_preview": self.get_description_preview(),
            "books_count": self.get_books_count(),
            "is_popular": self.is_popular_genre(),
            "average_rating": self.get_average_rating(),
            "created_at": self.created_at
        }