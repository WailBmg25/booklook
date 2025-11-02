# Technology Stack

## Core Framework

- **FastAPI**: Modern Python web framework for building APIs
- **Python 3.13**: Primary language (3.11+ supported)
- **Uvicorn**: ASGI server for running FastAPI applications

## Database & ORM

- **PostgreSQL**: Primary database (version 15+ recommended)
- **SQLAlchemy 2.0**: ORM with declarative base
- **Alembic**: Database migrations
- **psycopg2-binary**: PostgreSQL adapter

## Caching & Performance

- **Redis**: Caching layer and session storage
- Connection pooling configured (pool_size=10, max_overflow=20)

## Configuration & Environment

- **Pydantic Settings**: Type-safe configuration management
- **python-dotenv**: Environment variable loading
- Environment files: `.env` for local, `environment.yml` for conda

## Development & Deployment

- **Docker Compose**: Local development environment
- **MiniConda**: Recommended Python environment manager
- **pgAdmin**: Database administration interface (optional)

## Common Commands

### Environment Setup

```bash
# Using conda (recommended)
conda create -n booklook python=3.13
conda activate booklook
pip install -r src/requirements.txt

# Or using conda environment file
conda env create -f src/environment.yml
conda activate book_library_env
```

### Development

```bash
# Start development server
uvicorn main:app --reload

# Start with Docker
docker-compose up -d

# Database migrations
alembic upgrade head
```

### Database Access

- PostgreSQL: localhost:5432 (bookuser/bookpass123)
- Redis: localhost:6379
- pgAdmin: localhost:5050 (admin@booklib.com/admin123)
