"""Services package - Now redirects to MVC Controllers.

This package now exports the new MVC controllers for clean architecture.
Use controllers directly for better code organization.
"""

# Import MVC controllers
from controllers import (
    BookController,
    UserController, 
    ReviewController,
    ReadingProgressController
)

# Export controllers through services for compatibility
BookService = BookController  # Alias for migration
UserService = UserController  # Alias for migration
ReviewService = ReviewController  # Alias for migration
ReadingProgressService = ReadingProgressController  # Alias for migration

__all__ = [
    # MVC Controllers (recommended)
    "BookController",
    "UserController",
    "ReviewController", 
    "ReadingProgressController",
    # Aliases for migration (use controllers directly instead)
    "BookService",
    "UserService", 
    "ReviewService",
    "ReadingProgressService"
]