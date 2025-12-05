"""Pydantic schemas for book-related requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AuthorInfo(BaseModel):
    """Author information schema."""
    id: int
    nom: str
    prenom: Optional[str] = None
    biographie: Optional[str] = None

    class Config:
        from_attributes = True


class GenreInfo(BaseModel):
    """Genre information schema."""
    id: int
    nom: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class BookResponse(BaseModel):
    """Response schema for book data."""
    id: int
    titre: str
    isbn: Optional[str] = None
    image_url: Optional[str] = None
    author_names: Optional[List[str]] = []
    genre_names: Optional[List[str]] = []
    date_publication: Optional[str] = None  # Changed from int to str to handle date objects
    description: Optional[str] = None
    average_rating: Optional[float] = 0.0
    review_count: Optional[int] = 0
    word_count: Optional[int] = None
    total_pages: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BookDetailResponse(BaseModel):
    """Detailed response schema for book with authors and genres."""
    id: int
    titre: str
    isbn: Optional[str] = None
    image_url: Optional[str] = None
    author_names: Optional[List[str]] = []
    genre_names: Optional[List[str]] = []
    date_publication: Optional[str] = None  # Changed from int to str to handle date objects
    description: Optional[str] = None
    average_rating: Optional[float] = 0.0
    review_count: Optional[int] = 0
    word_count: Optional[int] = None
    total_pages: Optional[int] = None
    created_at: Optional[datetime] = None
    authors: List[AuthorInfo] = []
    genres: List[GenreInfo] = []

    class Config:
        from_attributes = True


class PaginationInfo(BaseModel):
    """Pagination information schema."""
    total_count: int
    total_pages: int
    current_page: int
    page_size: int
    has_next: bool
    has_previous: bool


class BookListResponse(BaseModel):
    """Response schema for paginated book list."""
    books: List[BookResponse]
    pagination: PaginationInfo


class BookContentResponse(BaseModel):
    """Response schema for book content."""
    book_id: int
    book_title: str
    page: int
    total_pages: int
    content: str
    has_next: bool
    has_previous: bool
