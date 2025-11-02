from pydantic_settings import BaseSettings
from typing import Optional


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
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()