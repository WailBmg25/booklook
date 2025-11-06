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
        """Get paginated book content for reading."""
        pagination_result = self.validate_pagination(page, 1)
        if pagination_result["error"]:
            return pagination_result["response"]
        page = pagination_result["page"]
        
        cache_key = self.cache_helper.generate_cache_key("book_content", book_id=book_id, page=page, words_per_page=words_per_page)
        
        def fetch_content():
            book = self.book_repo.get_by_id(book_id)
            if not book:
                return None
            
            # Calculate total pages based on word count
            total_words = book.word_count or 50000
            total_pages = (total_words + words_per_page - 1) // words_per_page
            
            if page > total_pages:
                return None
            
            # Generate realistic paginated content
            start_word = (page - 1) * words_per_page
            end_word = min(start_word + words_per_page, total_words)
            
            # Generate sample content for this page
            content = self._generate_page_content(book, page, start_word, end_word, words_per_page)
            
            return {
                "book_id": book_id,
                "book_title": book.get_display_title(),
                "page": page,
                "total_pages": total_pages,
                "content": content,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }
        
        return self.get_cached_or_fetch(cache_key, fetch_content)
    
    def _generate_page_content(self, book: Book, page: int, start_word: int, end_word: int, words_per_page: int) -> str:
        """Generate realistic sample content for a book page."""
        # Sample paragraphs based on book genre
        genre = book.genre_names[0] if book.genre_names else "Fiction"
        
        content_templates = {
            "Fiction": [
                "The morning sun cast long shadows across the quiet street. Sarah walked slowly, her mind wandering through memories of yesterday.",
                "In the distance, church bells rang out, marking the hour. Time seemed to move differently here, as if the town itself existed in another era.",
                "She paused at the corner, watching as leaves danced in the autumn breeze. Everything felt both familiar and strange at once."
            ],
            "Science Fiction": [
                "The starship's engines hummed with barely contained power as it approached the outer rim of the galaxy.",
                "Captain Morrison studied the holographic display, analyzing the strange energy signatures emanating from the nearby nebula.",
                "In the depths of space, nothing was ever truly silent. The universe whispered its secrets to those who knew how to listen."
            ],
            "Fantasy": [
                "Magic crackled in the air as the ancient spell took hold. The wizard's eyes glowed with an otherworldly light.",
                "Beyond the mountains lay the Forbidden Forest, where creatures of legend still roamed free under the eternal twilight.",
                "The prophecy had spoken of this moment, when the chosen one would finally claim their destiny."
            ],
            "Programming": [
                "Understanding data structures is fundamental to writing efficient code. Let's explore how arrays and linked lists differ in memory allocation.",
                "The algorithm's time complexity can be analyzed using Big O notation. This helps us predict performance at scale.",
                "Clean code is not just about functionality—it's about readability, maintainability, and following established patterns."
            ]
        }
        
        # Get appropriate template
        templates = content_templates.get(genre, content_templates["Fiction"])
        
        # Generate paragraphs to fill the page
        paragraphs = []
        words_generated = 0
        paragraph_index = 0
        
        while words_generated < words_per_page:
            # Cycle through templates
            template = templates[paragraph_index % len(templates)]
            
            # Add page-specific variation
            paragraph = f"{template} [Page {page}, Section {paragraph_index + 1}]"
            
            # Add some additional sentences to make it more realistic
            additional_text = f" The narrative continues to unfold, revealing deeper layers of meaning with each passing moment. Characters develop and situations evolve in unexpected ways."
            paragraph += additional_text
            
            paragraphs.append(paragraph)
            words_generated += len(paragraph.split())
            paragraph_index += 1
        
        # Join paragraphs with double newlines
        content = "\n\n".join(paragraphs)
        
        # Add page header
        header = f"=== {book.get_display_title()} ===\nPage {page} of {(book.word_count or 50000) // words_per_page}\n\n"
        
        return header + content
    
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