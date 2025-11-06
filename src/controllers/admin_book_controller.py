"""Admin book controller for book management operations."""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from repositories import BookRepository
from models import Book
from helpers import ValidationHelper, ResponseHelper
from controllers.base_controller import BaseController
from datetime import datetime


class AdminBookController(BaseController):
    """Controller for admin book management operations."""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.book_repo = BookRepository(db)
    
    def create_book(
        self,
        titre: str,
        isbn: Optional[str] = None,
        author_names: Optional[list[str]] = None,
        genre_names: Optional[list[str]] = None,
        description: Optional[str] = None,
        date_publication: Optional[datetime] = None,
        nombre_pages: Optional[int] = None,
        langue: Optional[str] = None,
        editeur: Optional[str] = None,
        image_couverture_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new book."""
        # Validate required fields
        titre = ValidationHelper.sanitize_string(titre, 500)
        if not titre:
            return ResponseHelper.error_response("Title is required", code="INVALID_TITLE")
        
        # Sanitize optional fields
        isbn = ValidationHelper.sanitize_string(isbn, 20) if isbn else None
        description = ValidationHelper.sanitize_string(description, 5000) if description else None
        langue = ValidationHelper.sanitize_string(langue, 50) if langue else "en"
        editeur = ValidationHelper.sanitize_string(editeur, 200) if editeur else None
        image_couverture_url = ValidationHelper.sanitize_string(image_couverture_url, 500) if image_couverture_url else None
        
        # Validate ISBN if provided
        if isbn and self.book_repo.isbn_exists(isbn):
            return ResponseHelper.error_response("ISBN already exists", code="ISBN_EXISTS")
        
        # Create book
        book = Book(
            titre=titre,
            isbn=isbn,
            author_names=author_names or [],
            genre_names=genre_names or [],
            description=description,
            date_publication=date_publication,
            nombre_pages=nombre_pages,
            langue=langue,
            editeur=editeur,
            image_couverture_url=image_couverture_url,
            average_rating=0.0,
            review_count=0
        )
        
        self.db.add(book)
        self.db.commit()
        self.db.refresh(book)
        
        return {
            "success": True,
            "book": book.to_dict()
        }
    
    def update_book(
        self,
        book_id: int,
        titre: Optional[str] = None,
        isbn: Optional[str] = None,
        author_names: Optional[list[str]] = None,
        genre_names: Optional[list[str]] = None,
        description: Optional[str] = None,
        date_publication: Optional[datetime] = None,
        nombre_pages: Optional[int] = None,
        langue: Optional[str] = None,
        editeur: Optional[str] = None,
        image_couverture_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing book."""
        book = self.book_repo.get_by_id(book_id)
        if not book:
            return ResponseHelper.error_response("Book not found", code="BOOK_NOT_FOUND")
        
        # Update fields if provided
        if titre is not None:
            titre = ValidationHelper.sanitize_string(titre, 500)
            if not titre:
                return ResponseHelper.error_response("Title cannot be empty", code="INVALID_TITLE")
            book.titre = titre
        
        if isbn is not None:
            isbn = ValidationHelper.sanitize_string(isbn, 20)
            # Check if ISBN already exists for another book
            if isbn and isbn != book.isbn and self.book_repo.isbn_exists(isbn):
                return ResponseHelper.error_response("ISBN already exists", code="ISBN_EXISTS")
            book.isbn = isbn
        
        if author_names is not None:
            book.author_names = author_names
        
        if genre_names is not None:
            book.genre_names = genre_names
        
        if description is not None:
            book.description = ValidationHelper.sanitize_string(description, 5000)
        
        if date_publication is not None:
            book.date_publication = date_publication
        
        if nombre_pages is not None:
            book.nombre_pages = nombre_pages
        
        if langue is not None:
            book.langue = ValidationHelper.sanitize_string(langue, 50)
        
        if editeur is not None:
            book.editeur = ValidationHelper.sanitize_string(editeur, 200)
        
        if image_couverture_url is not None:
            book.image_couverture_url = ValidationHelper.sanitize_string(image_couverture_url, 500)
        
        self.db.commit()
        self.db.refresh(book)
        
        # Invalidate cache
        self.cache_helper.invalidate_book_cache(book_id)
        
        return {
            "success": True,
            "book": book.to_dict()
        }
    
    def delete_book(self, book_id: int) -> Dict[str, Any]:
        """Delete a book."""
        book = self.book_repo.get_by_id(book_id)
        if not book:
            return ResponseHelper.error_response("Book not found", code="BOOK_NOT_FOUND")
        
        # Delete book (cascade will handle related records)
        self.db.delete(book)
        self.db.commit()
        
        # Invalidate cache
        self.cache_helper.invalidate_book_cache(book_id)
        
        return {
            "success": True,
            "message": "Book deleted successfully"
        }
    
    def get_pending_books(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get books pending approval (placeholder for future workflow)."""
        # For now, return empty list as we don't have approval workflow yet
        # This can be extended when approval workflow is implemented
        return {
            "books": [],
            "total_count": 0,
            "total_pages": 0,
            "current_page": page,
            "page_size": page_size,
            "has_next": False,
            "has_previous": False
        }
    
    def bulk_update_genres(self, book_ids: list[int], genre_names: list[str]) -> Dict[str, Any]:
        """Bulk update genres for multiple books."""
        updated_count = 0
        
        for book_id in book_ids:
            book = self.book_repo.get_by_id(book_id)
            if book:
                book.genre_names = genre_names
                self.cache_helper.invalidate_book_cache(book_id)
                updated_count += 1
        
        self.db.commit()
        
        return {
            "success": True,
            "updated_count": updated_count,
            "total_requested": len(book_ids)
        }
    
    def bulk_update_authors(self, book_ids: list[int], author_names: list[str]) -> Dict[str, Any]:
        """Bulk update authors for multiple books."""
        updated_count = 0
        
        for book_id in book_ids:
            book = self.book_repo.get_by_id(book_id)
            if book:
                book.author_names = author_names
                self.cache_helper.invalidate_book_cache(book_id)
                updated_count += 1
        
        self.db.commit()
        
        return {
            "success": True,
            "updated_count": updated_count,
            "total_requested": len(book_ids)
        }
