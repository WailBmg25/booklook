"""Pydantic schemas for reading progress requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProgressUpdateRequest(BaseModel):
    """Request schema for updating reading progress."""
    current_page: int = Field(..., ge=1)
    total_pages: Optional[int] = Field(None, ge=1)


class BookInfo(BaseModel):
    """Book information for reading progress."""
    id: int
    titre: str
    author_names: Optional[List[str]] = []
    word_count: Optional[int] = None
    total_pages: Optional[int] = None

    class Config:
        from_attributes = True


class ReadingProgressResponse(BaseModel):
    """Response schema for reading progress data."""
    user_id: int
    book_id: int
    current_page: int
    total_pages: Optional[int] = None
    progress_percentage: float
    last_read_at: datetime
    book: Optional[BookInfo] = None

    class Config:
        from_attributes = True


class ReadingSessionResponse(BaseModel):
    """Response schema for reading session information."""
    book_id: int
    book_title: str
    current_page: int
    total_pages: Optional[int] = None
    progress_percentage: float
    current_word_position: int
    last_read_at: datetime
    estimated_time_remaining: Optional[int] = None
    reading_status: str
    pages_remaining: int
    book_info: Optional[dict] = None
