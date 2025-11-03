"""FastAPI routes for reading progress management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from controllers import ReadingProgressController
from schemas import (
    ReadingProgressResponse,
    ProgressUpdateRequest,
    ReadingSessionResponse
)
from routes.auth_routes import get_current_user

progress_router = APIRouter(
    prefix="/user/reading-progress",
    tags=["reading-progress"]
)


@progress_router.get("/{book_id}", response_model=ReadingProgressResponse)
async def get_reading_progress(
    book_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's reading progress for a specific book.
    
    - **book_id**: ID of the book
    
    Requires authentication.
    """
    controller = ReadingProgressController(db)
    progress_data = controller.get_reading_progress(
        user_id=current_user["id"],
        book_id=book_id
    )
    
    if not progress_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Reading progress not found", "code": "PROGRESS_NOT_FOUND"}
        )
    
    return ReadingProgressResponse(**progress_data)


@progress_router.put("/{book_id}", response_model=ReadingProgressResponse)
async def update_reading_progress(
    book_id: int,
    progress_data: ProgressUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user's reading progress for a book.
    
    - **book_id**: ID of the book
    - **current_page**: Current page number
    - **total_pages**: Total pages in the book (optional)
    
    Requires authentication.
    """
    controller = ReadingProgressController(db)
    result = controller.update_reading_progress(
        user_id=current_user["id"],
        book_id=book_id,
        current_page=progress_data.current_page,
        total_pages=progress_data.total_pages
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Failed to update reading progress", "code": "UPDATE_FAILED"}
        )
    
    # Check for validation errors
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )
    
    return ReadingProgressResponse(**result)


@progress_router.get("/{book_id}/session", response_model=ReadingSessionResponse)
async def get_reading_session(
    book_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get reading session information for resuming reading.
    
    - **book_id**: ID of the book
    
    Returns detailed session info including current position and estimated time remaining.
    Requires authentication.
    """
    controller = ReadingProgressController(db)
    session_data = controller.get_reading_session_info(
        user_id=current_user["id"],
        book_id=book_id
    )
    
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Reading session not found", "code": "SESSION_NOT_FOUND"}
        )
    
    return ReadingSessionResponse(**session_data)


@progress_router.get("-history", response_model=List[ReadingProgressResponse])
async def get_reading_history(
    limit: int = Query(default=20, ge=1, le=100),
    days_back: int = Query(default=30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's recent reading history.
    
    - **limit**: Maximum number of items to return (default: 20, max: 100)
    - **days_back**: Number of days to look back (default: 30, max: 365)
    
    Requires authentication.
    """
    controller = ReadingProgressController(db)
    history = controller.get_user_reading_history(
        user_id=current_user["id"],
        limit=limit,
        days_back=days_back
    )
    
    return [ReadingProgressResponse(**item) for item in history]


@progress_router.get("-currently-reading", response_model=List[ReadingProgressResponse])
async def get_currently_reading(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get books the user is currently reading.
    
    - **limit**: Maximum number of items to return (default: 10, max: 50)
    
    Returns books with progress between 1% and 99%.
    Requires authentication.
    """
    controller = ReadingProgressController(db)
    currently_reading = controller.get_currently_reading(
        user_id=current_user["id"],
        limit=limit
    )
    
    return [ReadingProgressResponse(**item) for item in currently_reading]


@progress_router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reading_progress(
    book_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete reading progress for a book.
    
    - **book_id**: ID of the book
    
    Requires authentication.
    """
    controller = ReadingProgressController(db)
    success = controller.delete_reading_progress(
        user_id=current_user["id"],
        book_id=book_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Reading progress not found", "code": "PROGRESS_NOT_FOUND"}
        )
    
    return None
