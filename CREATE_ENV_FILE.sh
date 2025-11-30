#!/bin/bash

# Script to create .env.production file for BookLook deployment
# Run this script: bash CREATE_ENV_FILE.sh

echo "Creating .env.production file..."

cat > .env.production << 'EOF'
# BookLook Production Environment Configuration

# =============================================================================
# APPLICATION SETTINGS
# =============================================================================
APP_NAME="BookLook"
DEBUG=false
LOG_LEVEL=info

# =============================================================================
# DATABASE CONFIGURATION (PostgreSQL)
# =============================================================================
POSTGRES_USER=bookuser
POSTGRES_PASSWORD=CHANGE_THIS_PASSWORD
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=book_library

# PostgreSQL Performance Tuning (adjust based on your RAM)
# For 8GB RAM:
POSTGRES_SHARED_BUFFERS=2GB
POSTGRES_EFFECTIVE_CACHE_SIZE=6GB
POSTGRES_MAINTENANCE_WORK_MEM=512MB
POSTGRES_WORK_MEM=16MB
POSTGRES_MAX_CONNECTIONS=100

# For 16GB RAM, use these instead:
# POSTGRES_SHARED_BUFFERS=4GB
# POSTGRES_EFFECTIVE_CACHE_SIZE=12GB
# POSTGRES_MAINTENANCE_WORK_MEM=1GB
# POSTGRES_WORK_MEM=32MB
# POSTGRES_MAX_CONNECTIONS=150

# For 32GB+ RAM, use these instead:
# POSTGRES_SHARED_BUFFERS=8GB
# POSTGRES_EFFECTIVE_CACHE_SIZE=24GB
# POSTGRES_MAINTENANCE_WORK_MEM=2GB
# POSTGRES_WORK_MEM=64MB
# POSTGRES_MAX_CONNECTIONS=200

# =============================================================================
# REDIS CONFIGURATION
# =============================================================================
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_MAX_MEMORY=1gb

# =============================================================================
# BACKEND API CONFIGURATION
# =============================================================================
BACKEND_PORT=8000
BACKEND_WORKERS=4
SECRET_KEY=CHANGE_THIS_SECRET_KEY

# CORS Origins (comma-separated, no spaces)
# For local testing:
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
# For production with domain:
# CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# =============================================================================
# FRONTEND CONFIGURATION
# =============================================================================
FRONTEND_PORT=3000

# API URL (used by frontend to connect to backend)
# For local testing:
NEXT_PUBLIC_API_URL=http://localhost:8000
# For production with domain:
# NEXT_PUBLIC_API_URL=https://yourdomain.com/api

# NextAuth Configuration
# For local testing:
NEXTAUTH_URL=http://localhost:3000
# For production with domain:
# NEXTAUTH_URL=https://yourdomain.com

NEXTAUTH_SECRET=CHANGE_THIS_NEXTAUTH_SECRET

# =============================================================================
# NGINX CONFIGURATION (if using nginx profile)
# =============================================================================
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443

EOF

echo ""
echo "✅ .env.production file created!"
echo ""
echo "⚠️  IMPORTANT: You must edit this file and change these values:"
echo ""
echo "1. POSTGRES_PASSWORD - Generate with: openssl rand -base64 32"
echo "2. SECRET_KEY - Generate with: openssl rand -hex 32"
echo "3. NEXTAUTH_SECRET - Generate with: openssl rand -base64 32"
echo ""
echo "Run these commands to generate the values:"
echo ""
echo "  openssl rand -base64 32  # For POSTGRES_PASSWORD"
echo "  openssl rand -hex 32     # For SECRET_KEY"
echo "  openssl rand -base64 32  # For NEXTAUTH_SECRET"
echo ""
echo "Then edit the file:"
echo "  nano .env.production"
echo ""
