"""Book controller for book-related business logic - CLEAN VERSION."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from repositories import BookRepository
from models import Book
from helpers import ValidationHelper, ResponseHelper
from controllers.base_controller import BaseController


class BookController(BaseController):
    """Controller for book business logic operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, cache_ttl=3600)
        self.book_repo = BookRepository(db)
    
    def get_books_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        genre_filter: Optional[List[str]] = None,
        author_filter: Optional[List[str]] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        min_rating: Optional[float] = None,
        sort_by: str = "titre",
        sort_order: str = "asc"
    ) -> Dict[str, Any]:
        """Get paginated list of books with filtering and search."""
        # Validate pagination
        pagination_result = self.validate_pagination(page, page_size)
        if pagination_result["error"]:
            return pagination_result["response"]
        page, page_size = pagination_result["page"], pagination_result["page_size"]
        
        # Validate search parameters
        search_val = ValidationHelper.validate_search_params(search, genre_filter, author_filter, year_from, year_to, min_rating)
        if not search_val["is_valid"]:
            return ResponseHelper.validation_error_response(search_val)
        
        # Validate sort parameters
        sort_result = self.validate_sort(sort_by, sort_order, ["titre", "average_rating", "created_at", "date_publication"])
        if sort_result["error"]:
            return sort_result["response"]
        sort_by, sort_order = sort_result["sort_by"], sort_result["sort_order"]
        
        # Use cache - filter out 'self' from locals
        cache_params = {k: v for k, v in locals().items() if k != 'self'}
        cache_key = self.cache_helper.generate_cache_key("books_paginated", **cache_params)
        
        def fetch_books():
            result = self.book_repo.advanced_search(search, genre_filter, author_filter, year_from, year_to, min_rating, page, page_size, sort_by, sort_order)
            result["books"] = [book.to_dict() for book in result.pop("items")]
            return result
        
        return self.get_cached_or_fetch(cache_key, fetch_books)
    
    def get_book_details(self, book_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed book information by ID."""
        cache_key = self.cache_helper.generate_cache_key("book_detail", book_id=book_id)
        
        def fetch_book_details():
            book_data = self.book_repo.get_with_authors_and_genres(book_id)
            if not book_data:
                return None
            
            book_dict = book_data["book"].to_dict()
            book_dict["authors"] = [{"id": a.id, "nom": a.nom, "prenom": a.prenom, "biographie": a.biographie} for a in book_data["authors"]]
            book_dict["genres"] = [{"id": g.id, "nom": g.nom, "description": g.description} for g in book_data["genres"]]
            return book_dict
        
        return self.get_cached_or_fetch(cache_key, fetch_book_details)
    
    def search_books(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform full-text search on books."""
        query = ValidationHelper.sanitize_string(query, max_length=200)
        if not query:
            return []
        
        cache_key = self.cache_helper.generate_cache_key("search_books", query=query, limit=limit)
        
        def fetch_search_results():
            books_with_rank = self.book_repo.search_fulltext(query, limit)
            return [{"search_rank": rank, **book.to_dict()} for book, rank in books_with_rank]
        
        return self.get_cached_or_fetch(cache_key, fetch_search_results, ttl=300)
    
    def get_popular_books(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular books."""
        cache_key = self.cache_helper.generate_cache_key("popular_books", limit=limit)
        
        def fetch_popular():
            books = self.book_repo.get_popular_books(limit)
            return [book.to_dict() for book in books]
        
        return self.get_cached_or_fetch(cache_key, fetch_popular, ttl=1800)
    
    def get_book_content(self, book_id: int, page: int = 1, words_per_page: int = 300) -> Optional[Dict[str, Any]]:
        """Get paginated book content from database."""
        from repositories.book_page_repository import BookPageRepository
        
        pagination_result = self.validate_pagination(page, 1)
        if pagination_result["error"]:
            return pagination_result["response"]
        page = pagination_result["page"]
        
        cache_key = self.cache_helper.generate_cache_key("book_content", book_id=book_id, page=page)
        
        def fetch_content():
            book = self.book_repo.get_by_id(book_id)
            if not book:
                return None
            
            # Initialize page repository
            page_repo = BookPageRepository(self.db)
            
            # Check if book has any content
            total_pages = page_repo.get_total_pages(book_id)
            if total_pages == 0:
                return {
                    "error": "NO_CONTENT",
                    "message": "This book has no content available yet. Content may be loading or unavailable."
                }
            
            # Validate page number
            if page > total_pages or page < 1:
                return None
            
            # Fetch the actual page from database
            book_page = page_repo.get_page_by_number(book_id, page)
            if not book_page:
                return None
            
            return {
                "book_id": book_id,
                "book_title": book.get_display_title(),
                "page": page,
                "total_pages": total_pages,
                "content": book_page.content,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }
        
        return self.get_cached_or_fetch(cache_key, fetch_content)

    def update_book_rating(self, book_id: int, avg_rating: float, review_count: int) -> bool:
        """Update book's rating statistics."""
        book = self.book_repo.get_by_id(book_id)
        if not book:
            return False
        
        book.update_rating_stats(avg_rating, review_count)
        self.db.commit()
        self.cache_helper.invalidate_book_cache(book_id)
        return True
    
    def get_books_by_genre(self, genre_names: List[str], limit: int = 20) -> List[Dict[str, Any]]:
        """Get books by genre."""
        books = self.book_repo.find_by_genre(genre_names, limit)
        return [book.to_dict() for book in books]
    
    def get_books_by_author(self, author_names: List[str], limit: int = 20) -> List[Dict[str, Any]]:
        """Get books by author."""
        books = self.book_repo.find_by_author(author_names, limit)
        return [book.to_dict() for book in books]
    
    def get_highly_rated_books(self, min_rating: float = 4.0, min_reviews: int = 5, limit: int = 20) -> List[Dict[str, Any]]:
        """Get highly rated books with sufficient reviews."""
        books = self.book_repo.find_by_rating_range(min_rating)
        filtered_books = [book for book in books if book.is_highly_rated(min_rating) and book.has_sufficient_reviews(min_reviews)][:limit]
        return [book.to_dict() for book in filtered_books]
    
    def invalidate_book_cache(self, book_id: int) -> None:
        """Invalidate cache entries for a specific book."""
        self.cache_helper.invalidate_book_cache(book_id)