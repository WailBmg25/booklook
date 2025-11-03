"""Authentication helper utilities."""

import bcrypt
import secrets
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from .redis_client import get_redis_client


class AuthHelper:
    """Helper class for authentication operations."""
    
    def __init__(self, session_ttl: int = 86400):  # 24 hours
        self.redis_client = get_redis_client()
        self.session_ttl = session_ttl
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def generate_session_token(self) -> str:
        """Generate secure session token."""
        return secrets.token_urlsafe(32)
    
    def store_session(self, user_id: int, token: str) -> None:
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
    
    def get_session(self, token: str) -> Optional[Dict]:
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
    
    def delete_session(self, token: str) -> None:
        """Delete session from Redis."""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.delete(f"session:{token}")
        except Exception:
            pass
    
    def invalidate_user_sessions(self, user_id: int) -> None:
        """Invalidate all sessions for a user."""
        if not self.redis_client:
            return
        
        try:
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
    
    def validate_email_format(self, email: str) -> bool:
        """Validate email format (basic validation)."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password strength."""
        issues = []
        
        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            issues.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one number")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "strength": "Strong" if len(issues) == 0 else "Weak"
        }