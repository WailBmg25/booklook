"""Author model with business logic methods."""

from sqlalchemy import Column, Integer, String, Text, Date, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from .associations import book_author_association


class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(255), nullable=False, index=True)
    prenom = Column(String(255), nullable=True)
    biographie = Column(Text, nullable=True)
    photo_url = Column(String(500), nullable=True)
    date_naissance = Column(Date, nullable=True)
    nationalite = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    livres = relationship("Book", secondary=book_author_association, back_populates="auteurs")

    def __repr__(self):
        return f"<Author(id={self.id}, nom='{self.nom} {self.prenom}')>"
    
    # Business Logic Methods
    def get_full_name(self) -> str:
        """Get author's full name."""
        return f"{self.prenom} {self.nom}".strip() if self.prenom else self.nom
    
    def get_display_name(self) -> str:
        """Get author's display name."""
        return self.get_full_name()
    
    def get_books_count(self) -> int:
        """Get count of books by this author."""
        return len(self.livres)
    
    def is_prolific_author(self, min_books: int = 5) -> bool:
        """Check if author is prolific (has written many books)."""
        return self.get_books_count() >= min_books
    
    def get_age(self) -> int:
        """Get author's age if birth date is available."""
        if not self.date_naissance:
            return 0
        
        from datetime import datetime
        today = datetime.now().date()
        return today.year - self.date_naissance.year - (
            (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day)
        )
    
    def has_biography(self) -> bool:
        """Check if author has a biography."""
        return bool(self.biographie and self.biographie.strip())
    
    def get_biography_preview(self, max_length: int = 200) -> str:
        """Get truncated biography for preview."""
        if not self.biographie:
            return ""
        
        if len(self.biographie) <= max_length:
            return self.biographie
        
        return self.biographie[:max_length].rsplit(' ', 1)[0] + "..."
    
    def to_dict(self) -> dict:
        """Convert author to dictionary for API responses."""
        return {
            "id": self.id,
            "nom": self.nom,
            "prenom": self.prenom,
            "full_name": self.get_full_name(),
            "display_name": self.get_display_name(),
            "biographie": self.biographie,
            "biography_preview": self.get_biography_preview(),
            "photo_url": self.photo_url,
            "date_naissance": self.date_naissance,
            "age": self.get_age() if self.date_naissance else None,
            "nationalite": self.nationalite,
            "books_count": self.get_books_count(),
            "is_prolific": self.is_prolific_author(),
            "created_at": self.created_at
        }