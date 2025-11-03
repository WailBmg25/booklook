"""User controller for user-related business logic."""

from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session
from repositories import UserRepository
from models import User
from helpers import AuthHelper, ValidationHelper, ResponseHelper
from controllers.base_controller import BaseController
from datetime import datetime, timedelta


class UserController(BaseController):
    """Controller for user business logic operations."""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.user_repo = UserRepository(db)
        self.auth_helper = AuthHelper()
    def register_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str
    ) -> Optional[Dict[str, Any]]:
        """Register a new user with business logic validation."""
        # Validate email format
        if not self.auth_helper.validate_email_format(email):
            return ResponseHelper.error_response("Invalid email format", code="INVALID_EMAIL")
        
        # Validate password strength
        password_validation = self.auth_helper.validate_password_strength(password)
        if not password_validation["is_valid"]:
            return ResponseHelper.error_response("Weak password", password_validation["issues"], "WEAK_PASSWORD")
        
        # Sanitize input
        email = ValidationHelper.sanitize_string(email, 255)
        first_name = ValidationHelper.sanitize_string(first_name, 100)
        last_name = ValidationHelper.sanitize_string(last_name, 100)
        
        if not email or not first_name or not last_name:
            return ResponseHelper.error_response("Invalid input data", code="INVALID_INPUT")
        
        # Check if user already exists
        if self.user_repo.email_exists(email):
            return ResponseHelper.error_response("Email already exists", code="EMAIL_EXISTS")
        
        # Hash password and create user
        password_hash = self.auth_helper.hash_password(password)
        user = self.user_repo.create_user(
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name
        )
        
        # Update legacy fields and commit
        user.update_legacy_fields()
        self.db.commit()
        
        return user.to_dict(include_sensitive=True)
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and create session."""
        # Validate and sanitize email
        email = ValidationHelper.sanitize_string(email, 255)
        if not email or not self.auth_helper.validate_email_format(email):
            return ResponseHelper.error_response("Invalid email format", code="INVALID_EMAIL")
        
        user = self.user_repo.find_active_by_email(email)
        
        if not user or not self.auth_helper.verify_password(password, user.password_hash):
            return ResponseHelper.error_response("Invalid credentials", code="AUTH_FAILED")
        
        # Generate session token
        token = self.auth_helper.generate_session_token()
        self.auth_helper.store_session(user.id, token)
        
        return {
            "user": user.to_dict(include_sensitive=True),
            "token": token,
            "expires_at": (datetime.utcnow() + timedelta(seconds=86400)).isoformat()
        }
    
    def get_user_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user by session token."""
        session_data = self.auth_helper.get_session(token)
        if not session_data:
            return None
        
        user_id = session_data.get("user_id")
        if not user_id:
            return None
        
        user = self.user_repo.get_by_id(user_id)
        
        if not user or not user.is_active:
            # Clean up invalid session
            self.auth_helper.delete_session(token)
            return None
        
        return user.to_dict(include_sensitive=True)
    
    def logout_user(self, token: str) -> bool:
        """Logout user by deleting session."""
        self.auth_helper.delete_session(token)
        return True
    
    def update_user_profile(
        self,
        user_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        photo_url: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update user profile using business logic."""
        # Sanitize input
        first_name = ValidationHelper.sanitize_string(first_name, 100)
        last_name = ValidationHelper.sanitize_string(last_name, 100)
        photo_url = ValidationHelper.sanitize_string(photo_url, 500)
        
        user = self.user_repo.update_profile(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            photo_url=photo_url
        )
        
        if not user:
            return None
        
        # Update legacy fields using model business logic
        user.update_legacy_fields()
        self.db.commit()
        
        return user.to_dict(include_sensitive=True)
    
    def add_favorite_book(self, user_id: int, book_id: int) -> bool:
        """Add book to user's favorites using business logic."""
        return self.user_repo.add_favorite_book(user_id, book_id)
    
    def remove_favorite_book(self, user_id: int, book_id: int) -> bool:
        """Remove book from user's favorites using business logic."""
        return self.user_repo.remove_favorite_book(user_id, book_id)
    
    def get_user_favorites(self, user_id: int, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get user's favorite books with pagination."""
        # Validate pagination
        pagination_result = self.validate_pagination(page, page_size)
        if pagination_result["error"]:
            return pagination_result["response"]
        
        page, page_size = pagination_result["page"], pagination_result["page_size"]
        result = self.user_repo.get_user_favorites_paginated(user_id, page, page_size)
        
        # Format response using base controller helper
        return self.format_paginated_response(result, lambda book: book.to_dict())
    
    def is_book_favorited(self, user_id: int, book_id: int) -> bool:
        """Check if book is in user's favorites."""
        return self.user_repo.is_book_favorited(user_id, book_id)
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> Dict[str, Any]:
        """Change user password with validation."""
        # Validate new password strength
        password_validation = self.auth_helper.validate_password_strength(new_password)
        if not password_validation["is_valid"]:
            return ResponseHelper.error_response("Weak password", password_validation["issues"], "WEAK_PASSWORD")
        
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return ResponseHelper.error_response("User not found", code="USER_NOT_FOUND")
        
        # Verify current password
        if not self.auth_helper.verify_password(current_password, user.password_hash):
            return ResponseHelper.error_response("Current password is incorrect", code="INVALID_PASSWORD")
        
        # Hash new password and update
        new_password_hash = self.auth_helper.hash_password(new_password)
        success = self.user_repo.update_password(user_id, new_password_hash)
        
        return {"success": success}
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user account and invalidate sessions."""
        success = self.user_repo.deactivate_user(user_id)
        
        if success:
            # Invalidate all sessions for this user
            self.auth_helper.invalidate_user_sessions(user_id)
        
        return success
    
    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user statistics."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return {}
        
        # Get basic stats from repository
        basic_stats = self.user_repo.get_user_statistics(user_id)
        
        # Add business logic calculations using model methods
        enhanced_stats = {
            **basic_stats,
            "full_name": user.get_full_name(),
            "display_name": user.get_display_name(),
            "is_active_reviewer": user.is_active_reviewer(),
            "average_rating_given": user.get_average_rating_given()
        }
        
        return enhanced_stats
    
    def search_users(self, name_query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search users by name."""
        users = self.user_repo.get_users_by_name(name_query, limit)
        return [user.to_public_dict() for user in users]
    
    def get_user_profile(self, user_id: int, include_sensitive: bool = False) -> Optional[Dict[str, Any]]:
        """Get user profile with business logic."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return None
        
        return user.to_dict(include_sensitive=include_sensitive)
    
    def validate_email_format(self, email: str) -> bool:
        """Validate email format."""
        return self.auth_helper.validate_email_format(email)
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password strength."""
        return self.auth_helper.validate_password_strength(password)