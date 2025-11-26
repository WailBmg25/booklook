"""Book model with business logic methods."""

from sqlalchemy import Column, Integer, String, Text, Date, Float, DateTime, ARRAY, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from .associations import book_author_association, book_genre_association, user_favorite_association


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    titre = Column(String(500), nullable=False, index=True)
    isbn = Column(String(20), unique=True, nullable=False, index=True)
    date_publication = Column(Date, nullable=True)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    nombre_pages = Column(Integer, nullable=True)
    langue = Column(String(50), default="Français")
    editeur = Column(String(255), nullable=True)
    note_moyenne = Column(Float, default=0.0)
    nombre_reviews = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Enhanced fields for large dataset optimization
    author_names = Column(ARRAY(String), nullable=True, index=True)  # Denormalized author names
    genre_names = Column(ARRAY(String), nullable=True, index=True)   # Denormalized genre names
    content_path = Column(String(500), nullable=True)               # Path to book content file
    word_count = Column(Integer, nullable=True)                     # Total word count
    total_pages = Column(Integer, nullable=True)                    # Total pages for reading progress
    average_rating = Column(Numeric(3, 2), default=0)              # More precise rating (0.00-5.00)
    review_count = Column(Integer, default=0)                      # Cached review count

    # Relations
    auteurs = relationship("Author", secondary=book_author_association, back_populates="livres")
    genres = relationship("Genre", secondary=book_genre_association, back_populates="livres")
    reviews = relationship("Review", back_populates="book", foreign_keys="Review.book_id", cascade="all, delete-orphan")
    favoris_par = relationship("User", secondary=user_favorite_association, back_populates="livres_favoris")
    pages = relationship("BookPage", back_populates="book", cascade="all, delete-orphan", order_by="BookPage.page_number")

    def __repr__(self):
        return f"<Book(id={self.id}, titre='{self.titre}', isbn='{self.isbn}')>"
    
    # Business Logic Methods
    def update_rating_stats(self, avg_rating: float, review_count: int) -> None:
        """Update book's rating statistics."""
        self.average_rating = avg_rating
        self.review_count = review_count
        # Update legacy fields for backward compatibility
        self.note_moyenne = avg_rating
        self.nombre_reviews = review_count
    
    def calculate_progress_percentage(self, current_page: int) -> float:
        """Calculate reading progress percentage."""
        total_pages = self.total_pages or self.nombre_pages
        if not total_pages or total_pages <= 0:
            return 0.0
        return min(100.0, (current_page / total_pages) * 100)
    
    def get_display_title(self) -> str:
        """Get formatted title for display."""
        return self.titre.title() if self.titre else "Unknown Title"
    
    def get_author_display(self) -> str:
        """Get formatted author names for display."""
        if self.author_names:
            return ", ".join(self.author_names)
        return "Unknown Author"
    
    def get_genre_display(self) -> str:
        """Get formatted genre names for display."""
        if self.genre_names:
            return ", ".join(self.genre_names)
        return "Uncategorized"
    
    def is_highly_rated(self, threshold: float = 4.0) -> bool:
        """Check if book is highly rated."""
        return (self.average_rating or 0) >= threshold
    
    def has_sufficient_reviews(self, min_reviews: int = 5) -> bool:
        """Check if book has sufficient reviews for reliable rating."""
        return (self.review_count or 0) >= min_reviews
    
    def get_publication_year(self) -> int:
        """Get publication year."""
        return self.date_publication.year if self.date_publication else 0
    
    def is_recent_publication(self, years_back: int = 5) -> bool:
        """Check if book was published recently."""
        from datetime import datetime
        if not self.date_publication:
            return False
        current_year = datetime.now().year
        return (current_year - self.get_publication_year()) <= years_back
    
    def get_reading_difficulty(self) -> str:
        """Estimate reading difficulty based on word count and pages."""
        if not self.word_count or not self.total_pages:
            return "Unknown"
        
        words_per_page = self.word_count / self.total_pages
        
        if words_per_page < 200:
            return "Easy"
        elif words_per_page < 350:
            return "Medium"
        else:
            return "Difficult"
    
    def get_estimated_reading_time(self, words_per_minute: int = 200) -> int:
        """Get estimated reading time in minutes."""
        if not self.word_count:
            return 0
        return self.word_count // words_per_minute
    
    def update_denormalized_fields(self) -> None:
        """Update denormalized fields from relationships."""
        # This would typically be called after updating relationships
        if self.auteurs:
            self.author_names = [f"{author.prenom} {author.nom}".strip() for author in self.auteurs]
        
        if self.genres:
            self.genre_names = [genre.nom for genre in self.genres]
    
    def get_page(self, page_number: int):
        """Get a specific page by page number."""
        return next((p for p in self.pages if p.page_number == page_number), None)
    
    def get_page_content(self, page_number: int) -> str:
        """Get content for a specific page."""
        page = self.get_page(page_number)
        return page.content if page else ""
    
    def get_total_pages_from_content(self) -> int:
        """Get total number of pages from stored content."""
        return len(self.pages) if self.pages else 0
    
    def has_content(self) -> bool:
        """Check if book has any content pages."""
        return len(self.pages) > 0 if self.pages else False
    
    def get_content_word_count(self) -> int:
        """Get total word count from all pages."""
        if not self.pages:
            return 0
        return sum(page.word_count for page in self.pages)
    
    def to_dict(self) -> dict:
        """Convert book to dictionary for API responses."""
        return {
            "id": self.id,
            "titre": self.titre,
            "isbn": self.isbn,
            "date_publication": self.date_publication,
            "description": self.description,
            "image_url": self.image_url,
            "nombre_pages": self.nombre_pages,
            "total_pages": self.total_pages,
            "langue": self.langue,
            "editeur": self.editeur,
            "average_rating": float(self.average_rating) if self.average_rating else 0.0,
            "review_count": self.review_count or 0,
            "author_names": self.author_names or [],
            "genre_names": self.genre_names or [],
            "word_count": self.word_count,
            "content_path": self.content_path,
            "has_content": self.has_content(),
            "pages_count": self.get_total_pages_from_content(),
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }