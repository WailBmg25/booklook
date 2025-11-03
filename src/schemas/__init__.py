"""Pydantic schemas for request/response models."""

from .book_schemas import (
    BookResponse,
    BookListResponse,
    BookDetailResponse,
    BookContentResponse,
    AuthorInfo,
    GenreInfo,
    PaginationInfo
)
from .user_schemas import (
    UserResponse,
    UserCreateRequest,
    UserUpdateRequest,
    LoginRequest,
    LoginResponse,
    UserProfileResponse
)
from .review_schemas import (
    ReviewResponse,
    ReviewCreateRequest,
    ReviewUpdateRequest,
    ReviewListResponse
)
from .reading_progress_schemas import (
    ReadingProgressResponse,
    ProgressUpdateRequest,
    ReadingSessionResponse
)

__all__ = [
    # Book schemas
    "BookResponse",
    "BookListResponse",
    "BookDetailResponse",
    "BookContentResponse",
    "AuthorInfo",
    "GenreInfo",
    "PaginationInfo",
    # User schemas
    "UserResponse",
    "UserCreateRequest",
    "UserUpdateRequest",
    "LoginRequest",
    "LoginResponse",
    "UserProfileResponse",
    # Review schemas
    "ReviewResponse",
    "ReviewCreateRequest",
    "ReviewUpdateRequest",
    "ReviewListResponse",
    # Reading progress schemas
    "ReadingProgressResponse",
    "ProgressUpdateRequest",
    "ReadingSessionResponse"
]
