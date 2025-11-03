"""Pydantic schemas for user-related requests and responses."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserCreateRequest(BaseModel):
    """Request schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)


class UserUpdateRequest(BaseModel):
    """Request schema for user profile update."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    photo_url: Optional[str] = Field(None, max_length=500)


class LoginRequest(BaseModel):
    """Request schema for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Response schema for user data."""
    id: int
    email: str
    first_name: str
    last_name: str
    photo_url: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    """Response schema for user profile with statistics."""
    id: int
    email: str
    first_name: str
    last_name: str
    full_name: str
    photo_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    favorites_count: Optional[int] = 0
    reviews_count: Optional[int] = 0
    books_in_progress: Optional[int] = 0

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Response schema for successful login."""
    user: UserResponse
    token: str
    expires_at: str
