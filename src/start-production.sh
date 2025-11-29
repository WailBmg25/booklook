#!/bin/bash
# Production startup script for BookLook API

set -e

echo "Starting BookLook API in production mode..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Calculate optimal worker count
WORKERS=${WORKERS:-$(python -c "import multiprocessing; print(multiprocessing.cpu_count() * 2 + 1)")}
echo "Starting with $WORKERS workers..."

# Start Gunicorn with Uvicorn workers
exec gunicorn main:app \
    --config gunicorn.conf.py \
    --workers $WORKERS \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --keep-alive 5 \
    --log-level info \
    --access-logfile - \
    --error-logfile -
