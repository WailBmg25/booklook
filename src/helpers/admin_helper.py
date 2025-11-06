"""Admin helper utilities for role checking and permissions."""

from typing import Optional, TYPE_CHECKING
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from models import User


class AdminHelper:
    """Helper class for admin-related operations."""
    
    @staticmethod
    def is_admin(user: Optional['User']) -> bool:
        """Check if user has admin privileges."""
        if not user:
            return False
        return getattr(user, 'is_admin', False) and user.is_active
    
    @staticmethod
    def require_admin(user: Optional['User']) -> bool:
        """Require admin privileges, raise exception if not admin."""
        if not AdminHelper.is_admin(user):
            return False
        return True
    
    @staticmethod
    def get_admin_user(db: Session, user_id: int) -> Optional['User']:
        """Get user and verify admin status."""
        from models import User
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not AdminHelper.is_admin(user):
            return None
        return user
    
    @staticmethod
    def promote_to_admin(db: Session, user_id: int) -> bool:
        """Promote user to admin role."""
        from models import User
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.is_admin = True
        db.commit()
        return True
    
    @staticmethod
    def revoke_admin(db: Session, user_id: int) -> bool:
        """Revoke admin role from user."""
        from models import User
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.is_admin = False
        db.commit()
        return True
    
    @staticmethod
    def get_all_admins(db: Session) -> list['User']:
        """Get all admin users."""
        from models import User
        return db.query(User).filter(User.is_admin == True, User.is_active == True).all()
    
    @staticmethod
    def count_admins(db: Session) -> int:
        """Count total number of admin users."""
        from models import User
        return db.query(User).filter(User.is_admin == True, User.is_active == True).count()
