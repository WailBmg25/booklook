"""Base controller with shared functionality."""

from typing import Any, Callable, Dict, Optional
from sqlalchemy.orm import Session
from helpers import CacheHelper, ValidationHelper, ResponseHelper


class BaseController:
    """Base controller class with common functionality."""
    
    def __init__(self, db: Session, cache_ttl: int = 3600):
        self.db = db
        self.cache_helper = CacheHelper(default_ttl=cache_ttl)
    
    def validate_pagination(self, page: int, page_size: int) -> Dict[str, Any]:
        """Validate pagination parameters and return validated values or error."""
        validation = ValidationHelper.validate_pagination(page, page_size)
        if not validation["is_valid"]:
            return {"error": True, "response": ResponseHelper.validation_error_response(validation)}
        return {
            "error": False,
            "page": validation["page"],
            "page_size": validation["page_size"]
        }
    
    def validate_sort(self, sort_by: str, sort_order: str, allowed_fields: list) -> Dict[str, Any]:
        """Validate sort parameters and return validated values or error."""
        validation = ValidationHelper.validate_sort_params(sort_by, sort_order, allowed_fields)
        if not validation["is_valid"]:
            return {"error": True, "response": ResponseHelper.validation_error_response(validation)}
        return {
            "error": False,
            "sort_by": validation["sort_by"],
            "sort_order": validation["sort_order"]
        }
    
    def get_cached_or_fetch(
        self,
        cache_key: str,
        fetch_func: Callable,
        ttl: Optional[int] = None
    ) -> Any:
        """Get data from cache or fetch using provided function."""
        # Try cache first
        cached = self.cache_helper.get(cache_key)
        if cached is not None:
            return cached
        
        # Fetch data
        data = fetch_func()
        
        # Cache if data exists
        if data is not None:
            self.cache_helper.set(cache_key, data, ttl)
        
        return data
    
    def format_paginated_response(
        self,
        result: Dict[str, Any],
        transform_func: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Format paginated repository result into standard response."""
        items = result["items"]
        
        # Transform items if function provided
        if transform_func:
            items = [transform_func(item) for item in items]
        
        return {
            "items": items,
            "total_count": result["total_count"],
            "total_pages": result["total_pages"],
            "current_page": result["current_page"],
            "page_size": result["page_size"],
            "has_next": result["has_next"],
            "has_previous": result["has_previous"]
        }
    
    def commit_and_invalidate_cache(self, *cache_keys: str) -> None:
        """Commit transaction and invalidate specified cache keys."""
        self.db.commit()
        for key in cache_keys:
            self.cache_helper.delete(key)
