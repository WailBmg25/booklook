"""API routes for book pages."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from database import get_db
from controllers.book_page_controller import BookPageController


router = APIRouter(prefix="/books", tags=["Book Pages"])


# Pydantic schemas
class PageCreate(BaseModel):
    page_number: int
    content: str


class PageUpdate(BaseModel):
    content: str


class BulkPagesCreate(BaseModel):
    pages: List[PageCreate]


# Routes
@router.get("/{book_id}/pages/{page_number}")
def get_book_page(
    book_id: int,
    page_number: int,
    db: Session = Depends(get_db)
):
    """Get a specific page of a book."""
    controller = BookPageController(db)
    result = controller.get_page(book_id, page_number)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page {page_number} not found for book {book_id}"
        )
    
    return result


@router.get("/{book_id}/pages")
def get_book_pages_list(
    book_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get list of pages for a book (without full content)."""
    controller = BookPageController(db)
    result = controller.get_book_pages(book_id, skip, limit)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book {book_id} not found"
        )
    
    return result


@router.get("/{book_id}/pages/range/{start_page}/{end_page}")
def get_page_range(
    book_id: int,
    start_page: int,
    end_page: int,
    db: Session = Depends(get_db)
):
    """Get a range of pages (useful for reading multiple pages at once)."""
    if start_page < 1 or end_page < start_page:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid page range"
        )
    
    if end_page - start_page > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page range too large (max 10 pages at once)"
        )
    
    controller = BookPageController(db)
    result = controller.get_page_range(book_id, start_page, end_page)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book {book_id} not found"
        )
    
    return {"book_id": book_id, "pages": result}


@router.post("/{book_id}/pages", status_code=status.HTTP_201_CREATED)
def create_book_page(
    book_id: int,
    page_data: PageCreate,
    db: Session = Depends(get_db)
):
    """Create a new page for a book."""
    controller = BookPageController(db)
    page = controller.create_page(book_id, page_data.page_number, page_data.content)
    
    if not page:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not create page (book not found or page already exists)"
        )
    
    return page.to_dict()


@router.post("/{book_id}/pages/bulk", status_code=status.HTTP_201_CREATED)
def create_book_pages_bulk(
    book_id: int,
    bulk_data: BulkPagesCreate,
    db: Session = Depends(get_db)
):
    """Create multiple pages at once."""
    controller = BookPageController(db)
    
    pages_data = [
        {"page_number": page.page_number, "content": page.content}
        for page in bulk_data.pages
    ]
    
    pages = controller.create_pages_bulk(book_id, pages_data)
    
    if not pages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not create pages (book not found)"
        )
    
    return {
        "book_id": book_id,
        "pages_created": len(pages),
        "message": f"Successfully created {len(pages)} pages"
    }


@router.put("/{book_id}/pages/{page_number}")
def update_book_page(
    book_id: int,
    page_number: int,
    page_data: PageUpdate,
    db: Session = Depends(get_db)
):
    """Update content of a specific page."""
    controller = BookPageController(db)
    page = controller.update_page(book_id, page_number, page_data.content)
    
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page {page_number} not found for book {book_id}"
        )
    
    return page.to_dict()


@router.delete("/{book_id}/pages/{page_number}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book_page(
    book_id: int,
    page_number: int,
    db: Session = Depends(get_db)
):
    """Delete a specific page."""
    controller = BookPageController(db)
    result = controller.delete_page(book_id, page_number)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page {page_number} not found for book {book_id}"
        )
    
    return None


@router.get("/{book_id}/search")
def search_in_book(
    book_id: int,
    q: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Search for text within a book's pages."""
    if not q or len(q) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query must be at least 3 characters"
        )
    
    controller = BookPageController(db)
    result = controller.search_in_book(book_id, q, limit)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book {book_id} not found"
        )
    
    return result


@router.get("/{book_id}/content/stats")
def get_book_content_stats(
    book_id: int,
    db: Session = Depends(get_db)
):
    """Get statistics about book content."""
    controller = BookPageController(db)
    result = controller.get_book_content_stats(book_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book {book_id} not found"
        )
    
    return result
