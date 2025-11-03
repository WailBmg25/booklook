"""FastAPI routes for review management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from controllers import ReviewController
from schemas import (
    ReviewResponse,
    ReviewCreateRequest,
    ReviewUpdateRequest,
    ReviewListResponse,
    PaginationInfo
)
from routes.auth_routes import get_current_user

review_router = APIRouter(
    prefix="/reviews",
    tags=["reviews"]
)


@review_router.post("/books/{book_id}", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    book_id: int,
    review_data: ReviewCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new review for a book.
    
    - **book_id**: ID of the book to review
    - **rating**: Rating from 1 to 5
    - **title**: Review title (optional)
    - **content**: Review content (optional)
    
    Requires authentication.
    """
    controller = ReviewController(db)
    result = controller.create_review(
        user_id=current_user["id"],
        book_id=book_id,
        rating=review_data.rating,
        title=review_data.title,
        content=review_data.content
    )
    
    # Check for errors
    if not result or "error" in result:
        status_code = status.HTTP_400_BAD_REQUEST
        if result and result.get("code") == "DUPLICATE_REVIEW":
            status_code = status.HTTP_409_CONFLICT
        
        raise HTTPException(
            status_code=status_code,
            detail=result or {"error": "Failed to create review", "code": "CREATE_FAILED"}
        )
    
    return ReviewResponse(**result)


@review_router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific review by ID.
    
    - **review_id**: ID of the review to retrieve
    """
    controller = ReviewController(db)
    review_data = controller.get_review_details(review_id)
    
    if not review_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Review not found", "code": "REVIEW_NOT_FOUND"}
        )
    
    return ReviewResponse(**review_data)


@review_router.put("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: int,
    review_data: ReviewUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing review.
    
    - **review_id**: ID of the review to update
    - **rating**: Updated rating (optional)
    - **title**: Updated title (optional)
    - **content**: Updated content (optional)
    
    Requires authentication. Users can only update their own reviews.
    """
    controller = ReviewController(db)
    result = controller.update_review(
        review_id=review_id,
        user_id=current_user["id"],
        rating=review_data.rating,
        title=review_data.title,
        content=review_data.content
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Review not found or unauthorized", "code": "REVIEW_NOT_FOUND"}
        )
    
    # Check for validation errors
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )
    
    return ReviewResponse(**result)


@review_router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a review.
    
    - **review_id**: ID of the review to delete
    
    Requires authentication. Users can only delete their own reviews.
    """
    controller = ReviewController(db)
    success = controller.delete_review(
        review_id=review_id,
        user_id=current_user["id"]
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Review not found or unauthorized", "code": "REVIEW_NOT_FOUND"}
        )
    
    return None


@review_router.get("/user/my-reviews", response_model=ReviewListResponse)
async def get_user_reviews(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's review history.
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 10, max: 50)
    
    Requires authentication.
    """
    controller = ReviewController(db)
    result = controller.get_user_reviews(
        user_id=current_user["id"],
        page=page,
        page_size=page_size
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


@review_router.get("/books/{book_id}/user-review", response_model=ReviewResponse)
async def get_user_review_for_book(
    book_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's review for a specific book.
    
    - **book_id**: ID of the book
    
    Requires authentication.
    """
    controller = ReviewController(db)
    review_data = controller.get_user_review_for_book(
        user_id=current_user["id"],
        book_id=book_id
    )
    
    if not review_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Review not found", "code": "REVIEW_NOT_FOUND"}
        )
    
    return ReviewResponse(**review_data)
