"""Admin user management routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

from database import get_db
from controllers.admin_user_controller import AdminUserController
from middleware import require_admin
from models import User


router = APIRouter(prefix="/admin/users", tags=["Admin - Users"])


# Request/Response Models
class PasswordResetRequest(BaseModel):
    """Request model for password reset."""
    new_password: str = Field(..., min_length=8)


@router.get("")
async def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_admin: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Get paginated list of users with filtering (Admin only)."""
    controller = AdminUserController(db)
    return controller.get_users_paginated(
        page=page,
        page_size=page_size,
        search=search,
        is_active=is_active,
        is_admin=is_admin
    )


@router.get("/{user_id}")
async def get_user_details(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Get detailed user information (Admin only)."""
    controller = AdminUserController(db)
    result = controller.get_user_details(user_id)
    
    if result.get("error_code"):
        raise HTTPException(status_code=404, detail=result.get("message", "User not found"))
    
    return result


@router.put("/{user_id}/suspend")
async def suspend_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Suspend a user account (Admin only)."""
    # Prevent self-suspension
    if user_id == admin_user.id:
        raise HTTPException(status_code=400, detail="Cannot suspend your own account")
    
    controller = AdminUserController(db)
    result = controller.suspend_user(user_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message", "User not found"))
    
    return result


@router.put("/{user_id}/activate")
async def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Activate a user account (Admin only)."""
    controller = AdminUserController(db)
    result = controller.activate_user(user_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message", "User not found"))
    
    return result


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Delete a user account permanently (Admin only)."""
    # Prevent self-deletion
    if user_id == admin_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    controller = AdminUserController(db)
    result = controller.delete_user(user_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message", "User not found"))
    
    return result


@router.put("/{user_id}/promote")
async def promote_to_admin(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Promote user to admin role (Admin only)."""
    controller = AdminUserController(db)
    result = controller.promote_to_admin(user_id)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Failed to promote user")
        )
    
    return result


@router.put("/{user_id}/revoke-admin")
async def revoke_admin(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Revoke admin role from user (Admin only)."""
    # Prevent self-demotion
    if user_id == admin_user.id:
        raise HTTPException(status_code=400, detail="Cannot revoke your own admin role")
    
    controller = AdminUserController(db)
    result = controller.revoke_admin(user_id)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Failed to revoke admin role")
        )
    
    return result


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: int,
    request: PasswordResetRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Reset user password (Admin only)."""
    controller = AdminUserController(db)
    result = controller.reset_user_password(user_id, request.new_password)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Failed to reset password")
        )
    
    return result
