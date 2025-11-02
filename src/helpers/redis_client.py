"""Redis client configuration and connection management."""

import redis
from typing import Optional
from helpers.config import settings


class RedisClient:
    """Redis client singleton for caching operations."""
    
    _instance: Optional[redis.Redis] = None
    
    @classmethod
    def get_client(cls) -> Optional[redis.Redis]:
        """Get Redis client instance."""
        if cls._instance is None:
            try:
                cls._instance = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                # Test connection
                cls._instance.ping()
            except Exception as e:
                print(f"Redis connection failed: {e}")
                cls._instance = None
        
        return cls._instance
    
    @classmethod
    def close_connection(cls) -> None:
        """Close Redis connection."""
        if cls._instance:
            cls._instance.close()
            cls._instance = None


# Convenience function to get Redis client
def get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client instance."""
    return RedisClient.get_client()