"""FastAPI routes for authentication and user management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from controllers import UserController
from schemas import (
    UserCreateRequest,
    UserUpdateRequest,
    LoginRequest,
    LoginResponse,
    UserResponse,
    UserProfileResponse,
    BookResponse,
    BookListResponse,
    PaginationInfo
)

auth_router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

user_router = APIRouter(
    prefix="/user",
    tags=["user"]
)


# Helper function to get current user from token
async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> dict:
    """Get current user from authorization token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Missing or invalid authorization header", "code": "UNAUTHORIZED"}
        )
    
    token = authorization.replace("Bearer ", "")
    controller = UserController(db)
    user_data = controller.get_user_by_token(token)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid or expired token", "code": "INVALID_TOKEN"}
        )
    
    return user_data


@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    - **email**: Valid email address
    - **password**: Password (min 8 characters, must include uppercase, lowercase, and number)
    - **first_name**: User's first name
    - **last_name**: User's last name
    """
    controller = UserController(db)
    result = controller.register_user(
        email=user_data.email,
        password=user_data.password,
        first_name=user_data.first_name,
        last_name=user_data.last_name
    )
    
    # Check for errors
    if "error" in result:
        status_code = status.HTTP_400_BAD_REQUEST
        if result.get("code") == "EMAIL_EXISTS":
            status_code = status.HTTP_409_CONFLICT
        
        raise HTTPException(
            status_code=status_code,
            detail=result
        )
    
    return UserResponse(**result)


@auth_router.post("/login", response_model=LoginResponse)
async def login_user(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and create session.
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns user data and authentication token.
    """
    controller = UserController(db)
    result = controller.authenticate_user(
        email=login_data.email,
        password=login_data.password
    )
    
    # Check for errors
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result
        )
    
    return LoginResponse(**result)


@auth_router.post("/logout")
async def logout_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Logout user and invalidate session.
    
    Requires Authorization header with Bearer token.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Missing or invalid authorization header", "code": "UNAUTHORIZED"}
        )
    
    token = authorization.replace("Bearer ", "")
    controller = UserController(db)
    controller.logout_user(token)
    
    return {"message": "Successfully logged out"}


@user_router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's profile with statistics.
    
    Requires authentication.
    """
    controller = UserController(db)
    stats = controller.get_user_statistics(current_user["id"])
    
    # Merge user data with statistics
    profile_data = {**current_user, **stats}
    
    return UserProfileResponse(**profile_data)


@user_router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    update_data: UserUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile.
    
    - **first_name**: Updated first name (optional)
    - **last_name**: Updated last name (optional)
    - **photo_url**: Updated photo URL (optional)
    
    Requires authentication.
    """
    controller = UserController(db)
    result = controller.update_user_profile(
        user_id=current_user["id"],
        first_name=update_data.first_name,
        last_name=update_data.last_name,
        photo_url=update_data.photo_url
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "User not found", "code": "USER_NOT_FOUND"}
        )
    
    return UserResponse(**result)


@user_router.get("/favorites", response_model=BookListResponse)
async def get_user_favorites(
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's favorite books.
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    
    Requires authentication.
    """
    controller = UserController(db)
    result = controller.get_user_favorites(
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
    books = [BookResponse(**book) for book in result["items"]]
    pagination = PaginationInfo(
        total_count=result["total_count"],
        total_pages=result["total_pages"],
        current_page=result["current_page"],
        page_size=result["page_size"],
        has_next=result["has_next"],
        has_previous=result["has_previous"]
    )
    
    return BookListResponse(books=books, pagination=pagination)


@user_router.post("/favorites/{book_id}", status_code=status.HTTP_201_CREATED)
async def add_favorite_book(
    book_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a book to user's favorites.
    
    - **book_id**: ID of the book to add to favorites
    
    Requires authentication.
    """
    controller = UserController(db)
    success = controller.add_favorite_book(
        user_id=current_user["id"],
        book_id=book_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Failed to add book to favorites. Book may not exist or already in favorites.", "code": "ADD_FAVORITE_FAILED"}
        )
    
    return {"message": "Book added to favorites", "book_id": book_id}


@user_router.delete("/favorites/{book_id}")
async def remove_favorite_book(
    book_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a book from user's favorites.
    
    - **book_id**: ID of the book to remove from favorites
    
    Requires authentication.
    """
    controller = UserController(db)
    success = controller.remove_favorite_book(
        user_id=current_user["id"],
        book_id=book_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Book not found in favorites", "code": "FAVORITE_NOT_FOUND"}
        )
    
    return {"message": "Book removed from favorites", "book_id": book_id}


@user_router.get("/favorites/{book_id}/check")
async def check_favorite_status(
    book_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if a book is in user's favorites.
    
    - **book_id**: ID of the book to check
    
    Requires authentication.
    """
    controller = UserController(db)
    is_favorited = controller.is_book_favorited(
        user_id=current_user["id"],
        book_id=book_id
    )
    
    return {"book_id": book_id, "is_favorited": is_favorited}
