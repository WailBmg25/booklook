"""Admin authentication middleware for protected routes."""

from typing import Optional
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from helpers import AuthHelper, AdminHelper
from models import User


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user from authorization token."""
    if not authorization:
        return None
    
    # Extract token from "Bearer <token>" format
    token = authorization.replace("Bearer ", "").strip()
    
    auth_helper = AuthHelper()
    session_data = auth_helper.get_session(token)
    
    if not session_data:
        return None
    
    user_id = session_data.get("user_id")
    if not user_id:
        return None
    
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    return user


async def require_auth(
    current_user: Optional[User] = Depends(get_current_user)
) -> User:
    """Require authentication for route."""
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    return current_user


async def require_admin(
    current_user: User = Depends(require_auth)
) -> User:
    """Require admin privileges for route."""
    if not AdminHelper.is_admin(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    return current_user


async def optional_auth(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Optional authentication - returns user if authenticated, None otherwise."""
    return await get_current_user(authorization, db)
