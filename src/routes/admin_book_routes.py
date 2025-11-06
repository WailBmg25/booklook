"""Admin book management routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from database import get_db
from controllers.admin_book_controller import AdminBookController
from middleware import require_admin
from models import User


router = APIRouter(prefix="/admin/books", tags=["Admin - Books"])


# Request/Response Models
class BookCreateRequest(BaseModel):
    """Request model for creating a book."""
    titre: str = Field(..., min_length=1, max_length=500)
    isbn: Optional[str] = Field(None, max_length=20)
    author_names: Optional[List[str]] = Field(default_factory=list)
    genre_names: Optional[List[str]] = Field(default_factory=list)
    description: Optional[str] = Field(None, max_length=5000)
    date_publication: Optional[datetime] = None
    nombre_pages: Optional[int] = Field(None, gt=0)
    langue: Optional[str] = Field("en", max_length=50)
    editeur: Optional[str] = Field(None, max_length=200)
    image_couverture_url: Optional[str] = Field(None, max_length=500)


class BookUpdateRequest(BaseModel):
    """Request model for updating a book."""
    titre: Optional[str] = Field(None, min_length=1, max_length=500)
    isbn: Optional[str] = Field(None, max_length=20)
    author_names: Optional[List[str]] = None
    genre_names: Optional[List[str]] = None
    description: Optional[str] = Field(None, max_length=5000)
    date_publication: Optional[datetime] = None
    nombre_pages: Optional[int] = Field(None, gt=0)
    langue: Optional[str] = Field(None, max_length=50)
    editeur: Optional[str] = Field(None, max_length=200)
    image_couverture_url: Optional[str] = Field(None, max_length=500)


class BulkUpdateRequest(BaseModel):
    """Request model for bulk updates."""
    book_ids: List[int] = Field(..., min_items=1)
    genre_names: Optional[List[str]] = None
    author_names: Optional[List[str]] = None


@router.post("")
async def create_book(
    request: BookCreateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Create a new book (Admin only)."""
    controller = AdminBookController(db)
    result = controller.create_book(
        titre=request.titre,
        isbn=request.isbn,
        author_names=request.author_names,
        genre_names=request.genre_names,
        description=request.description,
        date_publication=request.date_publication,
        nombre_pages=request.nombre_pages,
        langue=request.langue,
        editeur=request.editeur,
        image_couverture_url=request.image_couverture_url
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to create book"))
    
    return result


@router.put("/{book_id}")
async def update_book(
    book_id: int,
    request: BookUpdateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Update an existing book (Admin only)."""
    controller = AdminBookController(db)
    result = controller.update_book(
        book_id=book_id,
        titre=request.titre,
        isbn=request.isbn,
        author_names=request.author_names,
        genre_names=request.genre_names,
        description=request.description,
        date_publication=request.date_publication,
        nombre_pages=request.nombre_pages,
        langue=request.langue,
        editeur=request.editeur,
        image_couverture_url=request.image_couverture_url
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to update book"))
    
    return result


@router.delete("/{book_id}")
async def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Delete a book (Admin only)."""
    controller = AdminBookController(db)
    result = controller.delete_book(book_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message", "Book not found"))
    
    return result


@router.get("/pending")
async def get_pending_books(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Get books pending approval (Admin only)."""
    controller = AdminBookController(db)
    return controller.get_pending_books(page, page_size)


@router.post("/bulk-update")
async def bulk_update_books(
    request: BulkUpdateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Bulk update books (Admin only)."""
    controller = AdminBookController(db)
    
    if request.genre_names is not None:
        result = controller.bulk_update_genres(request.book_ids, request.genre_names)
    elif request.author_names is not None:
        result = controller.bulk_update_authors(request.book_ids, request.author_names)
    else:
        raise HTTPException(status_code=400, detail="Either genre_names or author_names must be provided")
    
    return result
