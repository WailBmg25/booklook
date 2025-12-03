#!/bin/bash

# BookLook Deployment Script for ngrok Setup
# This script deploys BookLook with nginx as a single entry point for ngrok

set -e

echo "🚀 Starting BookLook deployment with nginx..."

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo "❌ Error: .env.production file not found!"
    echo "Please create it from .env.production.example"
    exit 1
fi

# Load environment variables
export $(cat .env.production | grep -v '^#' | xargs)

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down

# Build and start services
echo "🔨 Building and starting services..."
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Run ngrok on port 80: ngrok http 80"
echo "2. Update .env.production with your ngrok URL"
echo "3. Restart services: docker-compose -f docker-compose.prod.yml restart frontend"
echo ""
echo "🌐 Access points:"
echo "   - Nginx (for ngrok): http://localhost:80"
echo "   - Frontend direct: http://localhost:3000"
echo "   - Backend direct: http://localhost:8000"
echo "   - pgAdmin: http://localhost:5050"
echo ""
echo "📊 View logs: docker-compose -f docker-compose.prod.yml logs -f"
