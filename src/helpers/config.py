from pydantic_settings import BaseSettings
from typing import Optional, Union
from pydantic import field_validator, computed_field


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Book Library API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # PostgreSQL
    POSTGRES_USER: str = "bookuser"
    POSTGRES_PASSWORD: str = "bookpass123"
    POSTGRES_HOST: str = "localhost"  # "postgres" si dans Docker
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "book_library"
    
    # Redis
    REDIS_HOST: str = "localhost"  # "redis" si dans Docker
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    CACHE_TTL: int = 3600  # 1 heure en secondes
    
    # CORS - stored as string, parsed to list
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"
    
    def get_cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS string into a list."""
        if not self.CORS_ORIGINS or not self.CORS_ORIGINS.strip():
            return ["http://localhost:3000", "http://localhost:3001"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',') if origin.strip()]
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True
        # Allow environment variables to override .env file
        env_ignore_empty = True
        extra = 'ignore'


settings = Settings()