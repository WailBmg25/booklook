"""Pydantic schemas for review-related requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .book_schemas import PaginationInfo


class ReviewCreateRequest(BaseModel):
    """Request schema for creating a review."""
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = Field(None, max_length=5000)


class ReviewUpdateRequest(BaseModel):
    """Request schema for updating a review."""
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = Field(None, max_length=5000)


class UserInfo(BaseModel):
    """User information for review."""
    id: int
    first_name: str
    last_name: str
    full_name: str

    class Config:
        from_attributes = True


class BookInfo(BaseModel):
    """Book information for review."""
    id: int
    titre: str
    author_names: Optional[List[str]] = []

    class Config:
        from_attributes = True


class ReviewResponse(BaseModel):
    """Response schema for review data."""
    id: int
    user_id: int
    book_id: int
    rating: int
    title: Optional[str] = None
    content: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: Optional[UserInfo] = None
    book: Optional[BookInfo] = None

    class Config:
        from_attributes = True


class ReviewListResponse(BaseModel):
    """Response schema for paginated review list."""
    reviews: List[ReviewResponse]
    pagination: PaginationInfo
