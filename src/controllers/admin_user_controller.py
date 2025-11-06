"""Admin user controller for user management operations."""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from repositories import UserRepository
from models import User
from helpers import ValidationHelper, ResponseHelper, AuthHelper
from controllers.base_controller import BaseController


class AdminUserController(BaseController):
    """Controller for admin user management operations."""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.user_repo = UserRepository(db)
        self.auth_helper = AuthHelper()
    
    def get_users_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_admin: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Get paginated list of users with filtering."""
        # Validate pagination
        pagination_result = self.validate_pagination(page, page_size)
        if pagination_result["error"]:
            return pagination_result["response"]
        
        page, page_size = pagination_result["page"], pagination_result["page_size"]
        
        # Build query
        query = self.db.query(User)
        
        # Apply filters
        if search:
            search = ValidationHelper.sanitize_string(search, 200)
            search_pattern = f"%{search}%"
            query = query.filter(
                (User.email.ilike(search_pattern)) |
                (User.first_name.ilike(search_pattern)) |
                (User.last_name.ilike(search_pattern))
            )
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        if is_admin is not None:
            query = query.filter(User.is_admin == is_admin)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        users = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()
        
        # Calculate pagination metadata
        total_pages = (total_count + page_size - 1) // page_size
        
        return {
            "users": [user.to_dict(include_sensitive=True) for user in users],
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": page,
            "page_size": page_size,
            "has_next": page < total_pages,
            "has_previous": page > 1
        }
    
    def suspend_user(self, user_id: int) -> Dict[str, Any]:
        """Suspend a user account."""
        success = self.user_repo.deactivate_user(user_id)
        
        if not success:
            return ResponseHelper.error_response("User not found", code="USER_NOT_FOUND")
        
        # Invalidate all sessions for this user
        self.auth_helper.invalidate_user_sessions(user_id)
        
        return {
            "success": True,
            "message": "User suspended successfully"
        }
    
    def activate_user(self, user_id: int) -> Dict[str, Any]:
        """Activate a user account."""
        success = self.user_repo.activate_user(user_id)
        
        if not success:
            return ResponseHelper.error_response("User not found", code="USER_NOT_FOUND")
        
        return {
            "success": True,
            "message": "User activated successfully"
        }
    
    def delete_user(self, user_id: int) -> Dict[str, Any]:
        """Delete a user account permanently."""
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            return ResponseHelper.error_response("User not found", code="USER_NOT_FOUND")
        
        # Invalidate all sessions
        self.auth_helper.invalidate_user_sessions(user_id)
        
        # Delete user (cascade will handle related records)
        self.db.delete(user)
        self.db.commit()
        
        return {
            "success": True,
            "message": "User deleted successfully"
        }
    
    def promote_to_admin(self, user_id: int) -> Dict[str, Any]:
        """Promote user to admin role."""
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            return ResponseHelper.error_response("User not found", code="USER_NOT_FOUND")
        
        if user.is_admin:
            return ResponseHelper.error_response("User is already an admin", code="ALREADY_ADMIN")
        
        user.is_admin = True
        self.db.commit()
        
        return {
            "success": True,
            "message": "User promoted to admin successfully",
            "user": user.to_dict(include_sensitive=True)
        }
    
    def revoke_admin(self, user_id: int) -> Dict[str, Any]:
        """Revoke admin role from user."""
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            return ResponseHelper.error_response("User not found", code="USER_NOT_FOUND")
        
        if not user.is_admin:
            return ResponseHelper.error_response("User is not an admin", code="NOT_ADMIN")
        
        user.is_admin = False
        self.db.commit()
        
        return {
            "success": True,
            "message": "Admin role revoked successfully",
            "user": user.to_dict(include_sensitive=True)
        }
    
    def get_user_details(self, user_id: int) -> Dict[str, Any]:
        """Get detailed user information."""
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            return ResponseHelper.error_response("User not found", code="USER_NOT_FOUND")
        
        # Get user statistics
        stats = self.user_repo.get_user_statistics(user_id)
        
        user_data = user.to_dict(include_sensitive=True)
        user_data["statistics"] = stats
        
        return user_data
    
    def reset_user_password(self, user_id: int, new_password: str) -> Dict[str, Any]:
        """Reset user password (admin action)."""
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            return ResponseHelper.error_response("User not found", code="USER_NOT_FOUND")
        
        # Validate password strength
        password_validation = self.auth_helper.validate_password_strength(new_password)
        if not password_validation["is_valid"]:
            return ResponseHelper.error_response(
                "Weak password",
                password_validation["issues"],
                "WEAK_PASSWORD"
            )
        
        # Hash and update password
        new_password_hash = self.auth_helper.hash_password(new_password)
        success = self.user_repo.update_password(user_id, new_password_hash)
        
        if not success:
            return ResponseHelper.error_response("Failed to update password", code="UPDATE_FAILED")
        
        # Invalidate all sessions to force re-login
        self.auth_helper.invalidate_user_sessions(user_id)
        
        return {
            "success": True,
            "message": "Password reset successfully"
        }
