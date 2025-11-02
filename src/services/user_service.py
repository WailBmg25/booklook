"""User service for authentication and user management."""

from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from models.book import User, Book
from helpers.redis_client import get_redis_client
import bcrypt
import secrets
import json
from datetime import datetime, timedelta


class UserService:
    """Service for user authentication and management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.redis_client = get_redis_client()
        self.session_ttl = 86400  # 24 hours
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def _generate_session_token(self) -> str:
        """Generate secure session token."""
        return secrets.token_urlsafe(32)
    
    def _store_session(self, user_id: int, token: str) -> None:
        """Store session in Redis."""
        if not self.redis_client:
            return
        
        session_data = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(seconds=self.session_ttl)).isoformat()
        }
        
        try:
            self.redis_client.setex(
                f"session:{token}",
                self.session_ttl,
                json.dumps(session_data)
            )
        except Exception:
            pass
    
    def _get_session(self, token: str) -> Optional[Dict]:
        """Get session data from Redis."""
        if not self.redis_client:
            return None
        
        try:
            session_data = self.redis_client.get(f"session:{token}")
            if session_data:
                return json.loads(session_data)
        except Exception:
            pass
        return None
    
    def _delete_session(self, token: str) -> None:
        """Delete session from Redis."""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.delete(f"session:{token}")
        except Exception:
            pass
    
    def register_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str
    ) -> Optional[Dict]:
        """Register a new user."""
        # Check if user already exists
        existing_user = self.db.query(User).filter(User.email == email).first()
        if existing_user:
            return None
        
        # Hash password
        password_hash = self._hash_password(password)
        
        # Create user
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
        
        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "created_at": user.created_at
        }
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate user and create session."""
        user = self.db.query(User).filter(
            and_(User.email == email, User.is_active == True)
        ).first()
        
        if not user or not self._verify_password(password, user.password_hash):
            return None
        
        # Generate session token
        token = self._generate_session_token()
        self._store_session(user.id, token)
        
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,
                "created_at": user.created_at
            },
            "token": token,
            "expires_at": (datetime.utcnow() + timedelta(seconds=self.session_ttl)).isoformat()
        }
    
    def get_user_by_token(self, token: str) -> Optional[Dict]:
        """Get user by session token."""
        session_data = self._get_session(token)
        if not session_data:
            return None
        
        user_id = session_data.get("user_id")
        if not user_id:
            return None
        
        user = self.db.query(User).filter(
            and_(User.id == user_id, User.is_active == True)
        ).first()
        
        if not user:
            # Clean up invalid session
            self._delete_session(token)
            return None
        
        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "photo_url": user.photo_url
        }
    
    def logout_user(self, token: str) -> bool:
        """Logout user by deleting session."""
        self._delete_session(token)
        return True
    
    def update_user_profile(
        self,
        user_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        photo_url: Optional[str] = None
    ) -> Optional[Dict]:
        """Update user profile information."""
        user = self.db.query(User).filter(User.id == user_id).first()
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
        
        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "photo_url": user.photo_url,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
    
    def add_favorite_book(self, user_id: int, book_id: int) -> bool:
        """Add book to user's favorites."""
        user = self.db.query(User).filter(User.id == user_id).first()
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
        user = self.db.query(User).filter(User.id == user_id).first()
        book = self.db.query(Book).filter(Book.id == book_id).first()
        
        if not user or not book:
            return False
        
        if book in user.livres_favoris:
            user.livres_favoris.remove(book)
            self.db.commit()
        
        return True
    
    def get_user_favorites(self, user_id: int, page: int = 1, page_size: int = 20) -> Dict:
        """Get user's favorite books with pagination."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"books": [], "total_count": 0, "total_pages": 0}
        
        # Get total count
        total_count = len(user.livres_favoris)
        
        # Apply pagination
        offset = (page - 1) * page_size
        favorites = user.livres_favoris[offset:offset + page_size]
        
        books_list = []
        for book in favorites:
            book_dict = {
                "id": book.id,
                "titre": book.titre,
                "isbn": book.isbn,
                "image_url": book.image_url,
                "average_rating": float(book.average_rating) if book.average_rating else 0.0,
                "review_count": book.review_count or 0,
                "author_names": book.author_names or [],
                "genre_names": book.genre_names or []
            }
            books_list.append(book_dict)
        
        total_pages = (total_count + page_size - 1) // page_size
        
        return {
            "books": books_list,
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": page
        }
    
    def is_book_favorited(self, user_id: int, book_id: int) -> bool:
        """Check if book is in user's favorites."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        book = self.db.query(Book).filter(Book.id == book_id).first()
        if not book:
            return False
        
        return book in user.livres_favoris
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """Change user password."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Verify current password
        if not self._verify_password(current_password, user.password_hash):
            return False
        
        # Hash new password
        user.password_hash = self._hash_password(new_password)
        self.db.commit()
        
        return True
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user account."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.is_active = False
        self.db.commit()
        
        # Invalidate all sessions for this user
        if self.redis_client:
            try:
                # This is a simplified approach - in production you'd want to track user sessions
                pattern = f"session:*"
                keys = self.redis_client.keys(pattern)
                for key in keys:
                    session_data = self.redis_client.get(key)
                    if session_data:
                        data = json.loads(session_data)
                        if data.get("user_id") == user_id:
                            self.redis_client.delete(key)
            except Exception:
                pass
        
        return True