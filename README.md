# BookLook

A comprehensive book library application for managing and reading large book collections (400GB+ database support).

## Features

- 📚 **Book Management**: Browse, search, and filter books by genre, author, rating
- 📖 **Reading Interface**: Paginated book reader with progress tracking
- ⭐ **Reviews & Ratings**: User reviews with sentiment analysis
- 👤 **User Accounts**: Registration, authentication, and profile management
- ❤️ **Favorites**: Maintain personal book collections
- 🔐 **Admin Dashboard**: User, book, and review management
- 📊 **Analytics**: Book popularity and user activity metrics
- 🚀 **Performance**: Redis caching, optimized queries, connection pooling

## Quick Start

```bash
# Start all services (PostgreSQL, Redis, Backend, Frontend)
./start.sh

# Or start in production mode
./start.sh prod
```

**Access Points:**
- Frontend: http://localhost:3000
- Backend API: http://127.0.0.1:8000
- API Docs: http://127.0.0.1:8000/docs
- pgAdmin: http://localhost:5050

## Requirements

- Python 3.13+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose

## Installation

### 1. Install Python using Conda

```bash
# Download and install MiniConda
# https://docs.anaconda.com/free/miniconda/#quick-command-line-install

# Create environment
conda create -n booklook python=3.13
conda activate booklook

# Install backend dependencies
pip install -r src/requirements.txt
```

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 3. Start Docker Services

```bash
cd docker
docker-compose up -d
```

### 4. Run Database Migrations

```bash
cd src
alembic upgrade head
```

### 5. Start the Application

```bash
# From project root
./start.sh
```

## Documentation

📖 **[Complete Documentation](docs/README.md)**

### Quick Links

- [Quick Start Guide](docs/guides/QUICK_START.md)
- [Deployment Guide](docs/deployment/DEPLOYMENT_GUIDE.md)
- [Production Setup](docs/deployment/PRODUCTION_DEPLOYMENT.md)
- [Database Schema](docs/database/DATABASE_SCHEMA.sql)
- [Data Loading Guide](docs/database/DATA_LOADING_GUIDE.md)
- [Admin Dashboard](docs/admin/ADMIN_DASHBOARD_COMPLETE_SUMMARY.md)
- [Project Report](docs/reports/PROJECT_REPORT.md)

## Tech Stack

### Backend
- **Framework**: FastAPI
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **ORM**: SQLAlchemy 2.0
- **Server**: Gunicorn + Uvicorn
- **Migrations**: Alembic

### Frontend
- **Framework**: Next.js 16
- **UI**: React 19, Tailwind CSS
- **Auth**: NextAuth.js
- **HTTP Client**: Axios

## Project Structure

```
booklook/
├── src/                    # Backend (FastAPI)
│   ├── models/            # Database models
│   ├── repositories/      # Data access layer
│   ├── controllers/       # Business logic
│   ├── routes/            # API endpoints
│   ├── helpers/           # Utilities
│   └── tests/             # Backend tests
├── frontend/              # Frontend (Next.js)
│   ├── src/app/          # Pages and routes
│   ├── src/components/   # React components
│   ├── src/lib/          # API clients
│   └── e2e/              # E2E tests
├── docker/                # Docker configurations
├── docs/                  # Documentation
└── .kiro/                 # Kiro specs and workflows
```

## Development

### Backend Development

```bash
# Activate environment
conda activate booklook

# Run development server
python main.py

# Run tests
cd src && pytest

# Run with auto-reload
uvicorn main:app --reload
```

### Frontend Development

```bash
cd frontend
npm run dev
```

### Production Mode

```bash
# Start with Gunicorn (multiple workers)
./start.sh prod

# Or manually
cd src
./start-production.sh
```

## Testing

### Backend Tests (72 test cases)

```bash
cd src
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest tests/test_auth.py # Specific file
```

### Frontend Tests (15 E2E tests)

```bash
cd frontend
npm run test:e2e         # Run E2E tests
npm run test:e2e:ui      # Run with UI
```

## Data Loading

Load institutional datasets (400GB+):

```bash
# Load from CSV files
python load_institutional_dataset.py /path/to/csv/files

# With options
python load_institutional_dataset.py /path/to/csv \
    --batch-size 100 \
    --skip-existing \
    --no-fetch-isbn
```

## Deployment

See [Deployment Guide](docs/deployment/DEPLOYMENT_GUIDE.md) for:
- Docker deployment
- Google Cloud Platform
- Dedicated server setup
- Database optimization for 400GB+

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributors

- Wail Bmg

## Support

For issues and questions:
- Check the [Documentation](docs/README.md)
- Review [Project Report](docs/reports/PROJECT_REPORT.md)
- See [Quick Start Guide](docs/guides/QUICK_START.md)
