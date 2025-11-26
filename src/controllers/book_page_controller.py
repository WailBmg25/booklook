"""Controller for book page business logic."""

from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from repositories.book_page_repository import BookPageRepository
from repositories.book_repository import BookRepository
from models.book_page_model import BookPage


class BookPageController:
    """Controller for managing book pages."""
    
    def __init__(self, db: Session):
        self.db = db
        self.page_repo = BookPageRepository(db)
        self.book_repo = BookRepository(db)
    
    def get_page(self, book_id: int, page_number: int) -> Optional[Dict]:
        """Get a specific page with book information."""
        # Verify book exists
        book = self.book_repo.get_by_id(book_id)
        if not book:
            return None
        
        page = self.page_repo.get_page_by_number(book_id, page_number)
        if not page:
            return None
        
        # Get total pages for navigation
        total_pages = self.page_repo.get_total_pages(book_id)
        
        return {
            "page": page.to_dict(),
            "book": {
                "id": book.id,
                "titre": book.titre,
                "author_names": book.author_names,
                "total_pages": total_pages
            },
            "navigation": {
                "current_page": page_number,
                "total_pages": total_pages,
                "has_previous": page_number > 1,
                "has_next": page_number < total_pages,
                "previous_page": page_number - 1 if page_number > 1 else None,
                "next_page": page_number + 1 if page_number < total_pages else None
            }
        }
    
    def get_book_pages(self, book_id: int, skip: int = 0, limit: int = 50) -> Optional[Dict]:
        """Get paginated list of pages for a book."""
        book = self.book_repo.get_by_id(book_id)
        if not book:
            return None
        
        pages = self.page_repo.get_book_pages(book_id, skip, limit)
        total_pages = self.page_repo.get_total_pages(book_id)
        
        return {
            "book_id": book_id,
            "book_title": book.titre,
            "pages": [page.to_dict_without_content() for page in pages],
            "total_pages": total_pages,
            "skip": skip,
            "limit": limit
        }
    
    def get_page_range(self, book_id: int, start_page: int, end_page: int) -> Optional[List[Dict]]:
        """Get a range of pages (useful for reading multiple pages at once)."""
        book = self.book_repo.get_by_id(book_id)
        if not book:
            return None
        
        pages = self.page_repo.get_page_range(book_id, start_page, end_page)
        return [page.to_dict() for page in pages]
    
    def create_page(self, book_id: int, page_number: int, content: str) -> Optional[BookPage]:
        """Create a new page for a book."""
        # Verify book exists
        book = self.book_repo.get_by_id(book_id)
        if not book:
            return None
        
        # Check if page already exists
        if self.page_repo.page_exists(book_id, page_number):
            return None
        
        return self.page_repo.create_page(book_id, page_number, content)
    
    def create_pages_bulk(self, book_id: int, pages_data: List[Dict[str, any]]) -> Optional[List[BookPage]]:
        """Create multiple pages at once."""
        # Verify book exists
        book = self.book_repo.get_by_id(book_id)
        if not book:
            return None
        
        # Add book_id to each page data
        for page_data in pages_data:
            page_data['book_id'] = book_id
        
        pages = self.page_repo.create_pages_bulk(pages_data)
        
        # Update book's total_pages and word_count
        total_pages = self.page_repo.get_total_pages(book_id)
        total_words = self.page_repo.get_total_word_count(book_id)
        
        book.total_pages = total_pages
        book.word_count = total_words
        self.db.commit()
        
        return pages
    
    def update_page(self, book_id: int, page_number: int, content: str) -> Optional[BookPage]:
        """Update page content."""
        page = self.page_repo.update_page_content(book_id, page_number, content)
        
        if page:
            # Update book's word count
            total_words = self.page_repo.get_total_word_count(book_id)
            book = self.book_repo.get_by_id(book_id)
            if book:
                book.word_count = total_words
                self.db.commit()
        
        return page
    
    def delete_page(self, book_id: int, page_number: int) -> bool:
        """Delete a specific page."""
        result = self.page_repo.delete_page(book_id, page_number)
        
        if result:
            # Update book's total_pages and word_count
            book = self.book_repo.get_by_id(book_id)
            if book:
                total_pages = self.page_repo.get_total_pages(book_id)
                total_words = self.page_repo.get_total_word_count(book_id)
                book.total_pages = total_pages
                book.word_count = total_words
                self.db.commit()
        
        return result
    
    def search_in_book(self, book_id: int, search_query: str, limit: int = 10) -> Optional[Dict]:
        """Search for text within a book's pages."""
        book = self.book_repo.get_by_id(book_id)
        if not book:
            return None
        
        pages = self.page_repo.search_in_pages(book_id, search_query, limit)
        
        return {
            "book_id": book_id,
            "book_title": book.titre,
            "search_query": search_query,
            "results_count": len(pages),
            "pages": [
                {
                    "page_number": page.page_number,
                    "content_preview": page.get_content_preview(300),
                    "word_count": page.word_count
                }
                for page in pages
            ]
        }
    
    def get_book_content_stats(self, book_id: int) -> Optional[Dict]:
        """Get statistics about book content."""
        book = self.book_repo.get_by_id(book_id)
        if not book:
            return None
        
        total_pages = self.page_repo.get_total_pages(book_id)
        total_words = self.page_repo.get_total_word_count(book_id)
        first_page = self.page_repo.get_first_page(book_id)
        last_page = self.page_repo.get_last_page(book_id)
        
        avg_words_per_page = total_words / total_pages if total_pages > 0 else 0
        estimated_reading_time = total_words / 200  # 200 words per minute
        
        return {
            "book_id": book_id,
            "book_title": book.titre,
            "total_pages": total_pages,
            "total_words": total_words,
            "average_words_per_page": round(avg_words_per_page, 2),
            "estimated_reading_time_minutes": round(estimated_reading_time, 2),
            "has_content": total_pages > 0,
            "first_page_number": first_page.page_number if first_page else None,
            "last_page_number": last_page.page_number if last_page else None
        }
