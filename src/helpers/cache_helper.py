"""Cache helper utilities for Redis operations."""

from typing import Any, Optional
import json
import hashlib
from .redis_client import get_redis_client


class CacheHelper:
    """Helper class for caching operations."""
    
    def __init__(self, default_ttl: int = 3600):
        self.redis_client = get_redis_client()
        self.default_ttl = default_ttl
    
    def generate_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from parameters."""
        key_data = f"{prefix}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, cache_key: str) -> Optional[Any]:
        """Get data from Redis cache."""
        if not self.redis_client:
            return None
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception:
            pass
        return None
    
    def set(self, cache_key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Set data in Redis cache."""
        if not self.redis_client:
            return
        try:
            ttl = ttl or self.default_ttl
            self.redis_client.setex(cache_key, ttl, json.dumps(data, default=str))
        except Exception:
            pass
    
    def delete(self, cache_key: str) -> None:
        """Delete data from cache."""
        if not self.redis_client:
            return
        try:
            self.redis_client.delete(cache_key)
        except Exception:
            pass
    
    def delete_pattern(self, pattern: str) -> None:
        """Delete all keys matching pattern."""
        if not self.redis_client:
            return
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
        except Exception:
            pass
    
    def invalidate_book_cache(self, book_id: int) -> None:
        """Invalidate all cache entries for a specific book."""
        patterns = [
            f"*book*{book_id}*",
            "*books_paginated*",
            "*popular_books*",
            "*search_books*"
        ]
        for pattern in patterns:
            self.delete_pattern(pattern)
    
    def invalidate_user_cache(self, user_id: int) -> None:
        """Invalidate all cache entries for a specific user."""
        patterns = [
            f"*user*{user_id}*",
            "*user_favorites*",
            "*user_reviews*"
        ]
        for pattern in patterns:
            self.delete_pattern(pattern)