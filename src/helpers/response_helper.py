"""Response helper utilities for consistent API responses."""

from typing import Any, Dict, List, Optional


class ResponseHelper:
    """Helper class for standardized response formatting."""
    
    @staticmethod
    def success_response(data: Any, message: Optional[str] = None) -> Dict[str, Any]:
        """Create a success response."""
        response = {"success": True, "data": data}
        if message:
            response["message"] = message
        return response
    
    @staticmethod
    def error_response(message: str, issues: Optional[List[str]] = None, code: Optional[str] = None) -> Dict[str, Any]:
        """Create an error response."""
        response = {"error": message}
        if issues:
            response["issues"] = issues
        if code:
            response["code"] = code
        return response
    
    @staticmethod
    def paginated_response(
        items: List[Any],
        total_count: int,
        current_page: int,
        page_size: int
    ) -> Dict[str, Any]:
        """Create a paginated response."""
        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 0
        
        return {
            "items": items,
            "pagination": {
                "total_count": total_count,
                "total_pages": total_pages,
                "current_page": current_page,
                "page_size": page_size,
                "has_next": current_page < total_pages,
                "has_previous": current_page > 1
            }
        }
    
    @staticmethod
    def validation_error_response(validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create a validation error response from validation result."""
        return ResponseHelper.error_response(
            message="Validation failed",
            issues=validation_result.get("issues", []),
            code="VALIDATION_ERROR"
        )
