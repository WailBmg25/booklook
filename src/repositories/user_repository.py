"""User repository for user-related database operations."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from models import User, Book
from .base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for user data access operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, User)
    
    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email address."""
        return self.db.query(User).filter(User.email == email).first()
    
    def find_active_by_email(self, email: str) -> Optional[User]:
        """Find active user by email address."""
        return self.db.query(User).filter(
            and_(User.email == email, User.is_active == True)
        ).first()
    
    def email_exists(self, email: str) -> bool:
        """Check if email already exists."""
        return self.db.query(User).filter(User.email == email).first() is not None
    
    def create_user(
        self,
        email: str,
        password_hash: str,
        first_name: str,
        last_name: str
    ) -> User:
        """Create a new user with required fields."""
        user = User(
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            # Legacy fields for backward compatibility
            nom=last_name,
            prenom=first_name
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_profile(
        self,
        user_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        photo_url: Optional[str] = None
    ) -> Optional[User]:
        """Update user profile information."""
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        if first_name is not None:
            user.first_name = first_name
            user.prenom = first_name  # Update legacy field
        
        if last_name is not None:
            user.last_name = last_name
            user.nom = last_name  # Update legacy field
        
        if photo_url is not None:
            user.photo_url = photo_url
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_password(self, user_id: int, password_hash: str) -> bool:
        """Update user password hash."""
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        user.password_hash = password_hash
        self.db.commit()
        return True
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user account."""
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        user.is_active = False
        self.db.commit()
        return True
    
    def activate_user(self, user_id: int) -> bool:
        """Activate user account."""
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        user.is_active = True
        self.db.commit()
        return True
    
    def get_user_favorites(self, user_id: int) -> List[Book]:
        """Get user's favorite books."""
        user = self.get_by_id(user_id)
        if not user:
            return []
        
        return user.livres_favoris
    
    def add_favorite_book(self, user_id: int, book_id: int) -> bool:
        """Add book to user's favorites."""
        user = self.get_by_id(user_id)
        book = self.db.query(Book).filter(Book.id == book_id).first()
        
        if not user or not book:
            return False
        
        # Check if already in favorites
        if book in user.livres_favoris:
            return True  # Already favorited
        
        user.livres_favoris.append(book)
        self.db.commit()
        return True
    
    def remove_favorite_book(self, user_id: int, book_id: int) -> bool:
        """Remove book from user's favorites."""
        user = self.get_by_id(user_id)
        book = self.db.query(Book).filter(Book.id == book_id).first()
        
        if not user or not book:
            return False
        
        if book in user.livres_favoris:
            user.livres_favoris.remove(book)
            self.db.commit()
        
        return True
    
    def is_book_favorited(self, user_id: int, book_id: int) -> bool:
        """Check if book is in user's favorites."""
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        book = self.db.query(Book).filter(Book.id == book_id).first()
        if not book:
            return False
        
        return book in user.livres_favoris
    
    def get_user_favorites_paginated(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get user's favorite books with pagination."""
        user = self.get_by_id(user_id)
        if not user:
            return {
                "items": [],
                "total_count": 0,
                "total_pages": 0,
                "current_page": page,
                "page_size": page_size,
                "has_next": False,
                "has_previous": False
            }
        
        # Get total count
        total_count = len(user.livres_favoris)
        
        # Apply pagination
        offset = (page - 1) * page_size
        favorites = user.livres_favoris[offset:offset + page_size]
        
        total_pages = (total_count + page_size - 1) // page_size
        
        return {
            "items": favorites,
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": page,
            "page_size": page_size,
            "has_next": page < total_pages,
            "has_previous": page > 1
        }
    
    def get_active_users(self, limit: Optional[int] = None) -> List[User]:
        """Get all active users."""
        query = self.db.query(User).filter(User.is_active == True)
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def get_users_by_name(self, name_query: str, limit: int = 10) -> List[User]:
        """Search users by first name or last name."""
        return (
            self.db.query(User)
            .filter(
                and_(
                    User.is_active == True,
                    or_(
                        User.first_name.ilike(f"%{name_query}%"),
                        User.last_name.ilike(f"%{name_query}%")
                    )
                )
            )
            .limit(limit)
            .all()
        )
    
    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get basic statistics for a user."""
        user = self.get_by_id(user_id)
        if not user:
            return {}
        
        favorites_count = len(user.livres_favoris)
        reviews_count = len(user.reviews)
        
        return {
            "favorites_count": favorites_count,
            "reviews_count": reviews_count,
            "account_created": user.created_at,
            "last_updated": user.updated_at,
            "is_active": user.is_active
        }