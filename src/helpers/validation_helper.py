"""Validation helper utilities."""

from typing import Dict, Any, Optional, List


class ValidationHelper:
    """Helper class for data validation operations."""
    
    @staticmethod
    def validate_pagination(page: int, page_size: int, max_page_size: int = 100) -> Dict[str, Any]:
        """Validate pagination parameters."""
        issues = []
        
        if page < 1:
            issues.append("Page must be greater than 0")
        
        if page_size < 1:
            issues.append("Page size must be greater than 0")
        
        if page_size > max_page_size:
            issues.append(f"Page size cannot exceed {max_page_size}")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "page": max(1, page),
            "page_size": min(max(1, page_size), max_page_size)
        }
    
    @staticmethod
    def validate_rating(rating: int) -> Dict[str, Any]:
        """Validate rating value."""
        issues = []
        
        if not isinstance(rating, int):
            issues.append("Rating must be an integer")
        elif rating < 1 or rating > 5:
            issues.append("Rating must be between 1 and 5")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues
        }
    
    @staticmethod
    def validate_review_data(rating: int, title: Optional[str], content: Optional[str]) -> Dict[str, Any]:
        """Validate review data."""
        issues = []
        
        # Validate rating
        rating_validation = ValidationHelper.validate_rating(rating)
        if not rating_validation["is_valid"]:
            issues.extend(rating_validation["issues"])
        
        # Validate title length
        if title and len(title) > 200:
            issues.append("Title must be 200 characters or less")
        
        # Validate content length
        if content and len(content) > 5000:
            issues.append("Content must be 5000 characters or less")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues
        }
    
    @staticmethod
    def validate_search_params(
        search: Optional[str] = None,
        genre_filter: Optional[List[str]] = None,
        author_filter: Optional[List[str]] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        min_rating: Optional[float] = None
    ) -> Dict[str, Any]:
        """Validate search parameters."""
        issues = []
        
        # Validate search query length
        if search and len(search) > 200:
            issues.append("Search query must be 200 characters or less")
        
        # Validate year range
        if year_from and year_to and year_from > year_to:
            issues.append("Year from must be less than or equal to year to")
        
        # Validate rating range
        if min_rating and (min_rating < 0 or min_rating > 5):
            issues.append("Minimum rating must be between 0 and 5")
        
        # Validate filter arrays
        if genre_filter and len(genre_filter) > 10:
            issues.append("Cannot filter by more than 10 genres")
        
        if author_filter and len(author_filter) > 10:
            issues.append("Cannot filter by more than 10 authors")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues
        }
    
    @staticmethod
    def validate_reading_progress(current_page: int, total_pages: Optional[int] = None) -> Dict[str, Any]:
        """Validate reading progress data."""
        issues = []
        
        if current_page < 0:
            issues.append("Current page must be greater than or equal to 0")
        
        if total_pages and total_pages < 1:
            issues.append("Total pages must be greater than 0")
        
        if total_pages and current_page > total_pages:
            issues.append("Current page cannot exceed total pages")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues
        }
    
    @staticmethod
    def sanitize_string(value: Optional[str], max_length: Optional[int] = None) -> Optional[str]:
        """Sanitize string input."""
        if not value:
            return None
        
        # Strip whitespace
        sanitized = value.strip()
        
        # Truncate if needed
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized if sanitized else None
    
    @staticmethod
    def validate_sort_params(sort_by: str, sort_order: str, allowed_fields: List[str]) -> Dict[str, Any]:
        """Validate sorting parameters."""
        issues = []
        
        if sort_by not in allowed_fields:
            issues.append(f"Sort field must be one of: {', '.join(allowed_fields)}")
        
        if sort_order.lower() not in ["asc", "desc"]:
            issues.append("Sort order must be 'asc' or 'desc'")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "sort_by": sort_by if sort_by in allowed_fields else allowed_fields[0],
            "sort_order": sort_order.lower() if sort_order.lower() in ["asc", "desc"] else "asc"
        }