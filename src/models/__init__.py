"""Models package with separated model files for better organization."""

# Import association tables first (they're needed by models)
from .associations import (
    book_genre_association,
    book_author_association,
    user_favorite_association
)

# Import all models
from .book_model import Book
from .author_model import Author
from .genre_model import Genre
from .user_model import User
from .review_model import Review
from .reading_progress_model import ReadingProgress

__all__ = [
    # Association tables
    "book_genre_association",
    "book_author_association", 
    "user_favorite_association",
    # Models
    "Book",
    "Author",
    "Genre",
    "User",
    "Review",
    "ReadingProgress"
]