"""Book controller for book-related business logic - CLEAN VERSION."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from repositories import BookRepository
from models import Book
from helpers import CacheHelper, ValidationHelper


class BookController:
    """Controller for book business logic operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.book_repo = BookRepository(db)
        self.cache_helper = CacheHelper(default_ttl=3600)
    
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
        # Validate all parameters at once
        validation_errors = []
        
        pagination_val = ValidationHelper.validate_pagination(page, page_size)
        if not pagination_val["is_valid"]:
            validation_errors.extend(pagination_val["issues"])
        
        search_val = ValidationHelper.validate_search_params(search, genre_filter, author_filter, year_from, year_to, min_rating)
        if not search_val["is_valid"]:
            validation_errors.extend(search_val["issues"])
        
        sort_val = ValidationHelper.validate_sort_params(sort_by, sort_order, ["titre", "average_rating", "created_at", "date_publication"])
        if not sort_val["is_valid"]:
            validation_errors.extend(sort_val["issues"])
        
        if validation_errors:
            return {"error": "Validation failed", "issues": validation_errors}
        
        # Use validated parameters
        page, page_size = pagination_val["page"], pagination_val["page_size"]
        sort_by, sort_order = sort_val["sort_by"], sort_val["sort_order"]
        
        # Try cache
        cache_key = self.cache_helper.generate_cache_key("books_paginated", **locals())
        cached = self.cache_helper.get(cache_key)
        if cached:
            return cached
        
        # Get data from repository
        result = self.book_repo.advanced_search(search, genre_filter, author_filter, year_from, year_to, min_rating, page, page_size, sort_by, sort_order)
        
        # Format response
        response = {
            "books": [book.to_dict() for book in result["items"]],
            "total_count": result["total_count"],
            "total_pages": result["total_pages"],
            "current_page": result["current_page"],
            "page_size": result["page_size"],
            "has_next": result["has_next"],
            "has_previous": result["has_previous"]
        }
        
        self.cache_helper.set(cache_key, response)
        return response
    
    def get_book_details(self, book_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed book information by ID."""
        cache_key = self.cache_helper.generate_cache_key("book_detail", book_id=book_id)
        cached = self.cache_helper.get(cache_key)
        if cached:
            return cached
        
        book_data = self.book_repo.get_with_authors_and_genres(book_id)
        if not book_data:
            return None
        
        book_dict = book_data["book"].to_dict()
        book_dict["authors"] = [{"id": a.id, "nom": a.nom, "prenom": a.prenom, "biographie": a.biographie} for a in book_data["authors"]]
        book_dict["genres"] = [{"id": g.id, "nom": g.nom, "description": g.description} for g in book_data["genres"]]
        
        self.cache_helper.set(cache_key, book_dict)
        return book_dict
    
    def search_books(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform full-text search on books."""
        query = ValidationHelper.sanitize_string(query, max_length=200)
        if not query:
            return []
        
        cache_key = self.cache_helper.generate_cache_key("search_books", query=query, limit=limit)
        cached = self.cache_helper.get(cache_key)
        if cached:
            return cached
        
        books_with_rank = self.book_repo.search_fulltext(query, limit)
        results = [{"search_rank": rank, **book.to_dict()} for book, rank in books_with_rank]
        
        self.cache_helper.set(cache_key, results, ttl=300)  # 5 minutes
        return results
    
    def get_popular_books(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular books."""
        cache_key = self.cache_helper.generate_cache_key("popular_books", limit=limit)
        cached = self.cache_helper.get(cache_key)
        if cached:
            return cached
        
        books = self.book_repo.get_popular_books(limit)
        books_list = [book.to_dict() for book in books]
        
        self.cache_helper.set(cache_key, books_list, ttl=1800)  # 30 minutes
        return books_list
    
    def get_book_content(self, book_id: int, page: int = 1, words_per_page: int = 300) -> Optional[Dict[str, Any]]:
        """Get paginated book content for reading."""
        pagination_val = ValidationHelper.validate_pagination(page, 1)
        if not pagination_val["is_valid"]:
            return {"error": "Invalid page number"}
        
        page = pagination_val["page"]
        cache_key = self.cache_helper.generate_cache_key("book_content", book_id=book_id, page=page, words_per_page=words_per_page)
        cached = self.cache_helper.get(cache_key)
        if cached:
            return cached
        
        book = self.book_repo.get_by_id(book_id)
        if not book or not book.content_path:
            return None
        
        total_words = book.word_count or 50000
        total_pages = (total_words + words_per_page - 1) // words_per_page
        
        if page > total_pages:
            return None
        
        start_word = (page - 1) * words_per_page
        end_word = min(start_word + words_per_page, total_words)
        
        content_dict = {
            "book_id": book_id,
            "book_title": book.get_display_title(),
            "page": page,
            "total_pages": total_pages,
            "content": f"[Simulated content for {book.get_display_title()}, page {page}. Words {start_word}-{end_word}]",
            "has_next": page < total_pages,
            "has_previous": page > 1
        }
        
        self.cache_helper.set(cache_key, content_dict, ttl=3600)
        return content_dict
    
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