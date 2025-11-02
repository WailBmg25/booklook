# Project Structure

## Root Level

- `main.py`: FastAPI application entry point and router registration
- `README.md`: Project documentation and setup instructions
- `LICENSE`: Project license file

## Source Code (`src/`)

All application code resides in the `src/` directory following a modular architecture:

### Configuration

- `src/.env`: Local environment variables (not in git)
- `src/.env.example`: Environment template
- `src/requirements.txt`: Python dependencies
- `src/environment.yml`: Conda environment specification

### Core Modules

- `src/database.py`: SQLAlchemy engine, session management, and database utilities
- `src/helpers/`: Utility modules and shared functionality
  - `src/helpers/config.py`: Pydantic settings and configuration management
  - `src/helpers/__init__.py`: Helper module exports

### Data Layer

- `src/models/`: SQLAlchemy ORM models
  - `src/models/book.py`: Book, Author, Genre, Review, User models with relationships

### API Layer

- `src/routes/`: FastAPI route handlers organized by feature
  - `src/routes/__init__.py`: Router exports
  - `src/routes/base.py`: Base API routes (health checks, version info)

## Infrastructure (`docker/`)

- `docker/docker-compose.yml`: Local development environment with PostgreSQL, Redis, and pgAdmin

## Architecture Patterns

### Database Relationships

- Many-to-many: Books ↔ Authors, Books ↔ Genres, Users ↔ Favorite Books
- One-to-many: Books → Reviews, Users → Reviews
- Association tables with metadata (e.g., `user_favorites` includes `added_at`)

### Configuration Management

- Centralized settings in `src/helpers/config.py` using Pydantic
- Environment-specific overrides via `.env` files
- Type-safe configuration with defaults

### Import Conventions

- Relative imports within `src/` modules
- Absolute imports from root level (`from routes import base_router`)
- Helper utilities imported as modules (`from helpers import settings`)

### Naming Conventions

- French field names in models (e.g., `titre`, `auteurs`, `livres`)
- English for technical identifiers (e.g., `id`, `created_at`, `updated_at`)
- Snake_case for Python variables and functions
- PascalCase for SQLAlchemy model classes
