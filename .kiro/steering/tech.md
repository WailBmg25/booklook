# Technology Stack

## Core Technologies

- **Python**: 3.13+
- **Framework**: FastAPI for REST API
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Server**: Uvicorn

## Key Libraries

- `pydantic` & `pydantic-settings`: Configuration and data validation
- `bcrypt`: Password hashing
- `psycopg2-binary`: PostgreSQL adapter
- `python-dotenv`: Environment variable management
- `email-validator`: Email validation

## Environment Setup

### Using Conda (Recommended)

```bash
# Create environment
conda create -n booklook python=3.13
conda activate booklook

# Install dependencies
pip install -r src/requirements.txt
```

## Common Commands

### Database

```bash
# Run migrations
cd src
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback migration
alembic downgrade -1
```

### Docker Services

```bash
# Start PostgreSQL and Redis
cd docker
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f
```

### Development Server

```bash
# Run from project root
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Configuration

- Environment variables: `src/.env` (use `src/.env.example` as template)
- Settings managed via `src/helpers/config.py` using Pydantic Settings
- Database connection pooling: pool_size=10, max_overflow=20
- Default pagination: 20 items per page, max 100
