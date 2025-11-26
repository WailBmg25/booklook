"""Repository for book page data access."""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.book_page_model import BookPage
from repositories.base_repository import BaseRepository


class BookPageRepository(BaseRepository[BookPage]):
    """Repository for managing book page data."""
    
    def __init__(self, db: Session):
        super().__init__(db, BookPage)
    
    def get_book_pages(self, book_id: int, skip: int = 0, limit: int = 100) -> List[BookPage]:
        """Get all pages for a book with pagination."""
        return (
            self.db.query(BookPage)
            .filter(BookPage.book_id == book_id)
            .order_by(BookPage.page_number)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_page_by_number(self, book_id: int, page_number: int) -> Optional[BookPage]:
        """Get a specific page by book ID and page number."""
        return (
            self.db.query(BookPage)
            .filter(BookPage.book_id == book_id, BookPage.page_number == page_number)
            .first()
        )
    
    def get_total_pages(self, book_id: int) -> int:
        """Get total number of pages for a book."""
        return self.db.query(BookPage).filter(BookPage.book_id == book_id).count()
    
    def get_page_range(self, book_id: int, start_page: int, end_page: int) -> List[BookPage]:
        """Get a range of pages for a book."""
        return (
            self.db.query(BookPage)
            .filter(
                BookPage.book_id == book_id,
                BookPage.page_number >= start_page,
                BookPage.page_number <= end_page
            )
            .order_by(BookPage.page_number)
            .all()
        )
    
    def create_page(self, book_id: int, page_number: int, content: str) -> BookPage:
        """Create a new page for a book."""
        page = BookPage(
            book_id=book_id,
            page_number=page_number,
            content=content
        )
        page.calculate_word_count()
        
        self.db.add(page)
        self.db.commit()
        self.db.refresh(page)
        return page
    
    def create_pages_bulk(self, pages_data: List[dict]) -> List[BookPage]:
        """Create multiple pages at once."""
        pages = []
        for data in pages_data:
            page = BookPage(
                book_id=data['book_id'],
                page_number=data['page_number'],
                content=data['content']
            )
            page.calculate_word_count()
            pages.append(page)
        
        self.db.bulk_save_objects(pages, return_defaults=True)
        self.db.commit()
        return pages
    
    def update_page_content(self, book_id: int, page_number: int, content: str) -> Optional[BookPage]:
        """Update content of a specific page."""
        page = self.get_page_by_number(book_id, page_number)
        if page:
            page.content = content
            page.calculate_word_count()
            self.db.commit()
            self.db.refresh(page)
        return page
    
    def delete_book_pages(self, book_id: int) -> int:
        """Delete all pages for a book. Returns number of deleted pages."""
        count = self.db.query(BookPage).filter(BookPage.book_id == book_id).count()
        self.db.query(BookPage).filter(BookPage.book_id == book_id).delete()
        self.db.commit()
        return count
    
    def delete_page(self, book_id: int, page_number: int) -> bool:
        """Delete a specific page."""
        page = self.get_page_by_number(book_id, page_number)
        if page:
            self.db.delete(page)
            self.db.commit()
            return True
        return False
    
    def search_in_pages(self, book_id: int, search_query: str, limit: int = 10) -> List[BookPage]:
        """Search for text within book pages using full-text search."""
        return (
            self.db.query(BookPage)
            .filter(
                BookPage.book_id == book_id,
                func.to_tsvector('english', BookPage.content).match(search_query)
            )
            .order_by(BookPage.page_number)
            .limit(limit)
            .all()
        )
    
    def get_total_word_count(self, book_id: int) -> int:
        """Get total word count for all pages of a book."""
        result = (
            self.db.query(func.sum(BookPage.word_count))
            .filter(BookPage.book_id == book_id)
            .scalar()
        )
        return result or 0
    
    def get_first_page(self, book_id: int) -> Optional[BookPage]:
        """Get the first page of a book."""
        return (
            self.db.query(BookPage)
            .filter(BookPage.book_id == book_id)
            .order_by(BookPage.page_number)
            .first()
        )
    
    def get_last_page(self, book_id: int) -> Optional[BookPage]:
        """Get the last page of a book."""
        return (
            self.db.query(BookPage)
            .filter(BookPage.book_id == book_id)
            .order_by(BookPage.page_number.desc())
            .first()
        )
    
    def page_exists(self, book_id: int, page_number: int) -> bool:
        """Check if a specific page exists."""
        return (
            self.db.query(BookPage)
            .filter(BookPage.book_id == book_id, BookPage.page_number == page_number)
            .count() > 0
        )
