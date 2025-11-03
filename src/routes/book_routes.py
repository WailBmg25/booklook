"""FastAPI routes for book-related endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List
from database import get_db
from controllers import BookController, ReviewController
from schemas import (
    BookResponse,
    BookListResponse,
    BookDetailResponse,
    BookContentResponse,
    PaginationInfo,
    ReviewListResponse,
    ReviewResponse
)

book_router = APIRouter(
    prefix="/books",
    tags=["books"]
)


@book_router.get("", response_model=BookListResponse)
async def get_books(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    genre_filter: Optional[List[str]] = Query(default=None),
    author_filter: Optional[List[str]] = Query(default=None),
    year_from: Optional[int] = Query(default=None),
    year_to: Optional[int] = Query(default=None),
    min_rating: Optional[float] = Query(default=None, ge=0, le=5),
    sort_by: str = Query(default="titre"),
    sort_order: str = Query(default="asc"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of books with filtering and search.
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **search**: Search query for title/author
    - **genre_filter**: Filter by genres
    - **author_filter**: Filter by authors
    - **year_from**: Filter by publication year (from)
    - **year_to**: Filter by publication year (to)
    - **min_rating**: Minimum rating filter
    - **sort_by**: Sort field (titre, average_rating, created_at, date_publication)
    - **sort_order**: Sort order (asc, desc)
    """
    controller = BookController(db)
    result = controller.get_books_paginated(
        page=page,
        page_size=page_size,
        search=search,
        genre_filter=genre_filter,
        author_filter=author_filter,
        year_from=year_from,
        year_to=year_to,
        min_rating=min_rating,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # Check for validation errors
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )
    
    # Transform to response model
    books = [BookResponse(**book) for book in result.get("books", [])]
    pagination = PaginationInfo(
        total_count=result.get("total_count", 0),
        total_pages=result.get("total_pages", 0),
        current_page=result.get("current_page", 1),
        page_size=result.get("page_size", 20),
        has_next=result.get("has_next", False),
        has_previous=result.get("has_previous", False)
    )
    
    return BookListResponse(books=books, pagination=pagination)


@book_router.get("/{book_id}", response_model=BookDetailResponse)
async def get_book_details(
    book_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information for a specific book.
    
    - **book_id**: ID of the book to retrieve
    """
    controller = BookController(db)
    book_data = controller.get_book_details(book_id)
    
    if not book_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Book not found", "code": "BOOK_NOT_FOUND"}
        )
    
    return BookDetailResponse(**book_data)


@book_router.get("/{book_id}/content", response_model=BookContentResponse)
async def get_book_content(
    book_id: int,
    page: int = Query(default=1, ge=1),
    words_per_page: int = Query(default=300, ge=100, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get paginated book content for reading.
    
    - **book_id**: ID of the book
    - **page**: Content page number (default: 1)
    - **words_per_page**: Words per page (default: 300, range: 100-1000)
    """
    controller = BookController(db)
    content_data = controller.get_book_content(book_id, page, words_per_page)
    
    if not content_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Book content not found or page out of range", "code": "CONTENT_NOT_FOUND"}
        )
    
    # Check for validation errors
    if "error" in content_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=content_data
        )
    
    return BookContentResponse(**content_data)


@book_router.get("/{book_id}/reviews", response_model=ReviewListResponse)
async def get_book_reviews(
    book_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    db: Session = Depends(get_db)
):
    """
    Get reviews for a specific book.
    
    - **book_id**: ID of the book
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 10, max: 50)
    - **sort_by**: Sort field (created_at, rating, updated_at)
    - **sort_order**: Sort order (asc, desc)
    """
    controller = ReviewController(db)
    result = controller.get_book_reviews(
        book_id=book_id,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # Check for validation errors
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )
    
    # Transform to response model
    reviews = [ReviewResponse(**review) for review in result.get("reviews", [])]
    pagination = PaginationInfo(
        total_count=result.get("total_count", 0),
        total_pages=result.get("total_pages", 0),
        current_page=result.get("current_page", 1),
        page_size=result.get("page_size", 10),
        has_next=result.get("has_next", False),
        has_previous=result.get("has_previous", False)
    )
    
    return ReviewListResponse(reviews=reviews, pagination=pagination)
