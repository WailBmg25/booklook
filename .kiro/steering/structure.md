# Project Structure & Architecture

## MVC Architecture

BookLook follows a clean MVC (Model-View-Controller) pattern with repository layer for data access.

### Layer Responsibilities

- **Models** (`src/models/`): Domain entities with business logic, validation, and helper methods
- **Repositories** (`src/repositories/`): Pure data access layer, database queries, CRUD operations
- **Controllers** (`src/controllers/`): Business logic coordination, caching, cross-entity operations
- **Routes** (`src/routes/`): FastAPI endpoints, request/response handling
- **Helpers** (`src/helpers/`): Utilities for auth, caching, validation, and configuration

## Directory Structure

```
src/
├── models/                    # Domain models (one file per entity)
│   ├── associations.py        # Many-to-many relationship tables
│   ├── book_model.py
│   ├── author_model.py
│   ├── genre_model.py
│   ├── user_model.py
│   ├── review_model.py
│   └── reading_progress_model.py
├── repositories/              # Data access layer
│   ├── base_repository.py     # Common CRUD operations
│   ├── book_repository.py
│   ├── user_repository.py
│   ├── review_repository.py
│   └── reading_progress_repository.py
├── controllers/               # Business logic layer
│   ├── book_controller.py
│   ├── user_controller.py
│   ├── review_controller.py
│   └── reading_progress_controller.py
├── routes/                    # API endpoints
│   ├── base.py
│   └── __init__.py
├── helpers/                   # Utilities
│   ├── auth_helper.py
│   ├── cache_helper.py
│   ├── config.py
│   ├── redis_client.py
│   └── validation_helper.py
├── alembic/                   # Database migrations
│   └── versions/
├── database.py                # Database connection setup
└── requirements.txt
```

## Coding Conventions

### Import Order

1. Standard library imports
2. Third-party imports (FastAPI, SQLAlchemy, etc.)
3. Local application imports (models, repositories, controllers, helpers)

### Naming Conventions

- **Files**: snake_case with descriptive suffixes (`book_controller.py`, `user_model.py`)
- **Classes**: PascalCase (`BookController`, `UserRepository`)
- **Functions/Methods**: snake_case (`get_book_details`, `create_review`)
- **Constants**: UPPER_SNAKE_CASE (`DEFAULT_PAGE_SIZE`, `CACHE_TTL`)

### Database Sessions

- Use dependency injection: `db: Session = Depends(get_db)`
- Controllers receive db session in constructor
- Always close sessions properly (handled by FastAPI dependency)

### Business Logic Placement

- **Models**: Entity-specific logic (e.g., `book.is_highly_rated()`, `user.get_full_name()`)
- **Repositories**: Database queries only, no business logic
- **Controllers**: Orchestration, caching, validation, cross-entity operations
- **Routes**: Request/response handling, minimal logic

### Caching Strategy

- Use Redis for frequently accessed data
- Cache keys follow pattern: `entity:operation:id` (e.g., `book:details:123`)
- Default TTL: 3600 seconds (configurable via settings)
- Implement cache invalidation on updates/deletes

## Key Patterns

### Repository Pattern

```python
# Repositories handle all database operations
book_repo = BookRepository(db)
books = book_repo.find_by_genre(["Fiction"])
```

### Controller Pattern

```python
# Controllers coordinate business logic
book_controller = BookController(db)
result = book_controller.get_books_paginated(page=1, page_size=20)
```

### Model Enhancement

```python
# Models include business methods
book = Book(titre="Python Guide", rating=4.5)
book.is_highly_rated()  # Returns True if rating >= 4.0
book.to_dict()  # Clean serialization for API responses
```

## Migration Strategy

- Use Alembic for all schema changes
- Never modify database directly
- Test migrations on development before production
- Keep migration files in version control
