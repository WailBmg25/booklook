"""Book repository for book-related database operations."""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text, desc, asc
from models import Book, Author, Genre
from .base_repository import BaseRepository


class BookRepository(BaseRepository[Book]):
    """Repository for book data access operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, Book)
    
    def find_by_isbn(self, isbn: str) -> Optional[Book]:
        """Find book by ISBN."""
        return self.db.query(Book).filter(Book.isbn == isbn).first()
    
    def isbn_exists(self, isbn: str) -> bool:
        """Check if ISBN already exists."""
        return self.db.query(Book).filter(Book.isbn == isbn).first() is not None
    
    def search_by_title(self, title: str, limit: int = 10) -> List[Book]:
        """Search books by title using ILIKE."""
        return (
            self.db.query(Book)
            .filter(Book.titre.ilike(f"%{title}%"))
            .limit(limit)
            .all()
        )
    
    def search_fulltext(self, query: str, limit: int = 10) -> List[Tuple[Book, float]]:
        """Perform full-text search with ranking."""
        search_query = text("""
            SELECT b.*, 
                   ts_rank(to_tsvector('english', b.titre || ' ' || COALESCE(b.description, '')), 
                          plainto_tsquery('english', :query)) as rank
            FROM books b
            WHERE to_tsvector('english', b.titre || ' ' || COALESCE(b.description, '')) 
                  @@ plainto_tsquery('english', :query)
            ORDER BY rank DESC, b.average_rating DESC
            LIMIT :limit
        """)
        
        result = self.db.execute(search_query, {"query": query, "limit": limit})
        books_with_rank = []
        
        for row in result:
            book = self.db.query(Book).filter(Book.id == row.id).first()
            if book:
                books_with_rank.append((book, float(row.rank)))
        
        return books_with_rank
    
    def find_by_genre(self, genre_names: List[str], limit: int = 20) -> List[Book]:
        """Find books by genre names using array overlap."""
        return (
            self.db.query(Book)
            .filter(Book.genre_names.op('&&')(genre_names))
            .order_by(desc(Book.average_rating))
            .limit(limit)
            .all()
        )
    
    def find_by_author(self, author_names: List[str], limit: int = 20) -> List[Book]:
        """Find books by author names using array overlap."""
        return (
            self.db.query(Book)
            .filter(Book.author_names.op('&&')(author_names))
            .order_by(desc(Book.average_rating))
            .limit(limit)
            .all()
        )
    
    def find_by_year_range(self, year_from: int, year_to: int) -> List[Book]:
        """Find books published within year range."""
        return (
            self.db.query(Book)
            .filter(
                and_(
                    func.extract('year', Book.date_publication) >= year_from,
                    func.extract('year', Book.date_publication) <= year_to
                )
            )
            .order_by(desc(Book.date_publication))
            .all()
        )
    
    def find_by_rating_range(self, min_rating: float, max_rating: float = 5.0) -> List[Book]:
        """Find books within rating range."""
        return (
            self.db.query(Book)
            .filter(
                and_(
                    Book.average_rating >= min_rating,
                    Book.average_rating <= max_rating
                )
            )
            .order_by(desc(Book.average_rating))
            .all()
        )
    
    def get_popular_books(self, limit: int = 10) -> List[Book]:
        """Get most popular books based on rating and review count."""
        return (
            self.db.query(Book)
            .filter(Book.review_count > 0)
            .order_by(desc(Book.average_rating * func.log(Book.review_count + 1)))
            .limit(limit)
            .all()
        )
    
    def get_recent_books(self, limit: int = 10) -> List[Book]:
        """Get recently added books."""
        return (
            self.db.query(Book)
            .order_by(desc(Book.created_at))
            .limit(limit)
            .all()
        )
    
    def advanced_search(
        self,
        search_text: Optional[str] = None,
        genre_filter: Optional[List[str]] = None,
        author_filter: Optional[List[str]] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        min_rating: Optional[float] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "titre",
        sort_order: str = "asc"
    ) -> Dict[str, Any]:
        """Advanced search with multiple filters."""
        query = self.db.query(Book)
        
        # Apply search filter using partial text matching (ILIKE for case-insensitive partial match)
        if search_text:
            search_pattern = f"%{search_text}%"
            query = query.filter(
                or_(
                    Book.titre.ilike(search_pattern),
                    Book.description.ilike(search_pattern),
                    func.array_to_string(Book.author_names, ' ').ilike(search_pattern)
                )
            )
        
        # Apply genre filter
        if genre_filter:
            query = query.filter(Book.genre_names.op('&&')(genre_filter))
        
        # Apply author filter
        if author_filter:
            query = query.filter(Book.author_names.op('&&')(author_filter))
        
        # Apply year filters
        if year_from:
            query = query.filter(func.extract('year', Book.date_publication) >= year_from)
        if year_to:
            query = query.filter(func.extract('year', Book.date_publication) <= year_to)
        
        # Apply rating filter
        if min_rating:
            query = query.filter(Book.average_rating >= min_rating)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply sorting
        if hasattr(Book, sort_by):
            sort_column = getattr(Book, sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
        
        # Apply pagination
        offset = (page - 1) * page_size
        books = query.offset(offset).limit(page_size).all()
        
        total_pages = (total_count + page_size - 1) // page_size
        
        return {
            "items": books,
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": page,
            "page_size": page_size,
            "has_next": page < total_pages,
            "has_previous": page > 1
        }
    
    def get_with_authors_and_genres(self, book_id: int) -> Optional[Dict[str, Any]]:
        """Get book with related authors and genres."""
        book = self.get_by_id(book_id)
        if not book:
            return None
        
        # Get related authors and genres
        authors = self.db.query(Author).join(Book.auteurs).filter(Book.id == book_id).all()
        genres = self.db.query(Genre).join(Book.genres).filter(Book.id == book_id).all()
        
        return {
            "book": book,
            "authors": authors,
            "genres": genres
        }
    
    def update_rating_stats(self, book_id: int, avg_rating: float, review_count: int) -> bool:
        """Update book's rating statistics."""
        book = self.get_by_id(book_id)
        if not book:
            return False
        
        book.average_rating = avg_rating
        book.review_count = review_count
        # Update legacy fields
        book.note_moyenne = avg_rating
        book.nombre_reviews = review_count
        
        self.db.commit()
        return True
    
    def get_books_by_ids(self, book_ids: List[int]) -> List[Book]:
        """Get multiple books by their IDs."""
        return self.db.query(Book).filter(Book.id.in_(book_ids)).all()
    
    def get_genre_statistics(self) -> List[Dict[str, Any]]:
        """Get statistics about genres."""
        # This would require a more complex query to unnest the genre_names array
        # For now, return basic stats
        result = (
            self.db.query(
                func.count(Book.id).label('total_books'),
                func.avg(Book.average_rating).label('avg_rating')
            )
            .first()
        )
        
        return [{
            "total_books": result.total_books or 0,
            "average_rating": float(result.avg_rating) if result.avg_rating else 0.0
        }]