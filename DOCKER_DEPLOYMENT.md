# BookLook Docker Deployment Guide

This guide covers deploying BookLook using Docker and Docker Compose for production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Deployment Scripts](#deployment-scripts)
- [Service Architecture](#service-architecture)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows with WSL2
- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **RAM**: Minimum 8GB (16GB+ recommended for production)
- **Storage**: Minimum 100GB free space (more for large datasets)
- **CPU**: 4+ cores recommended

### Install Docker

#### Ubuntu/Debian

```bash
# Update package index
sudo apt-get update

# Install dependencies
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add your user to docker group
sudo usermod -aG docker $USER
```

#### macOS

```bash
# Install using Homebrew
brew install --cask docker

# Or download Docker Desktop from:
# https://www.docker.com/products/docker-desktop
```

### Verify Installation

```bash
docker --version
docker-compose --version
```

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd booklook
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.production.example .env.production

# Edit configuration (see Configuration section)
nano .env.production
```

**Important**: Update these critical values in `.env.production`:
- `POSTGRES_PASSWORD` - Strong database password
- `SECRET_KEY` - Generate with: `openssl rand -hex 32`
- `NEXTAUTH_SECRET` - Generate with: `openssl rand -base64 32`
- `CORS_ORIGINS` - Your domain(s)
- `NEXTAUTH_URL` - Your domain URL

### 3. Deploy

```bash
# Full deployment (build + start + migrate)
./deploy.sh deploy

# Or step by step:
./deploy.sh build    # Build images
./deploy.sh start    # Start services
./deploy.sh migrate  # Run migrations
```

### 4. Verify Deployment

```bash
# Check service health
./health-check.sh

# View service status
./deploy.sh status

# View logs
./logs.sh all
```

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Configuration

### Environment Files

Three environment templates are provided:

1. **`.env.development.example`** - Local development
2. **`.env.staging.example`** - Staging environment
3. **`.env.production.example`** - Production deployment

Copy the appropriate template to `.env.production` and configure:

```bash
cp .env.production.example .env.production
```

### Key Configuration Options

#### Database Settings

```bash
POSTGRES_USER=bookuser
POSTGRES_PASSWORD=<strong-password>
POSTGRES_DB=book_library

# Performance tuning (adjust based on server RAM)
POSTGRES_SHARED_BUFFERS=8GB          # 25% of RAM
POSTGRES_EFFECTIVE_CACHE_SIZE=24GB   # 75% of RAM
POSTGRES_MAINTENANCE_WORK_MEM=2GB
POSTGRES_WORK_MEM=32MB
POSTGRES_MAX_CONNECTIONS=200
```

#### Backend Settings

```bash
BACKEND_PORT=8000
BACKEND_WORKERS=8                    # 2 * CPU cores + 1
SECRET_KEY=<generate-random-key>
CORS_ORIGINS=https://yourdomain.com
```

#### Frontend Settings

```bash
FRONTEND_PORT=3000
NEXT_PUBLIC_API_URL=https://yourdomain.com/api
NEXTAUTH_URL=https://yourdomain.com
NEXTAUTH_SECRET=<generate-random-secret>
```

#### Redis Settings

```bash
REDIS_MAX_MEMORY=4gb
```

### Generate Secrets

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate NEXTAUTH_SECRET
openssl rand -base64 32
```

## Deployment Scripts

### deploy.sh

Main deployment script for managing the application.

```bash
# Full deployment
./deploy.sh deploy

# Start services
./deploy.sh start

# Stop services
./deploy.sh stop

# Restart services
./deploy.sh restart

# Build images
./deploy.sh build

# Check status
./deploy.sh status

# View logs
./deploy.sh logs [service]

# Run migrations
./deploy.sh migrate

# Health check
./deploy.sh health
```

### backup.sh

Database and volume backup management.

```bash
# Full backup (database + volumes)
./backup.sh full

# Database only
./backup.sh db

# Volumes only
./backup.sh volumes

# List backups
./backup.sh list

# Restore from backup
./backup.sh restore backups/booklook_db_20240101_120000.sql.gz

# Cleanup old backups (older than 30 days)
./backup.sh cleanup 30
```

### logs.sh

Easy log viewing for all services.

```bash
# View all logs
./logs.sh all

# View specific service logs
./logs.sh backend
./logs.sh frontend
./logs.sh postgres
./logs.sh redis

# Follow logs in real-time
./logs.sh backend 100 follow

# Show only errors
./logs.sh errors
./logs.sh errors backend
```

### health-check.sh

Comprehensive health checking.

```bash
# Full health check
./health-check.sh full

# Quick check
./health-check.sh quick

# Check specific service
./health-check.sh backend
./health-check.sh frontend
./health-check.sh database
./health-check.sh redis
```

## Service Architecture

### Services Overview

The application consists of 5 main services:

1. **PostgreSQL** - Primary database
2. **Redis** - Caching layer
3. **Backend** - FastAPI application
4. **Frontend** - Next.js application
5. **Nginx** - Reverse proxy (optional)

### Service Dependencies

```
Frontend → Backend → PostgreSQL
                  → Redis
Nginx → Frontend
     → Backend
```

### Ports

- **Frontend**: 3000
- **Backend**: 8000
- **PostgreSQL**: 5432
- **Redis**: 6379
- **Nginx**: 80, 443

### Volumes

- `postgres_data` - PostgreSQL data persistence
- `redis_data` - Redis data persistence
- `./logs` - Application logs

## Monitoring and Maintenance

### Regular Maintenance Tasks

#### Daily

```bash
# Check service health
./health-check.sh

# Check logs for errors
./logs.sh errors
```

#### Weekly

```bash
# Create backup
./backup.sh full

# Check disk space
df -h

# Check container stats
docker stats
```

#### Monthly

```bash
# Cleanup old backups
./backup.sh cleanup 30

# Update Docker images
docker-compose -f docker-compose.prod.yml pull
./deploy.sh restart
```

### Monitoring Commands

```bash
# View resource usage
docker stats

# View container details
docker-compose -f docker-compose.prod.yml ps

# Check logs
./logs.sh all 500

# Health check
./health-check.sh full
```

### Database Maintenance

```bash
# Connect to database
docker-compose -f docker-compose.prod.yml exec postgres psql -U bookuser -d book_library

# Run VACUUM
docker-compose -f docker-compose.prod.yml exec postgres psql -U bookuser -d book_library -c "VACUUM ANALYZE;"

# Check database size
docker-compose -f docker-compose.prod.yml exec postgres psql -U bookuser -d book_library -c "SELECT pg_size_pretty(pg_database_size('book_library'));"
```

## Troubleshooting

### Common Issues

#### Services Won't Start

```bash
# Check logs
./logs.sh all

# Check if ports are in use
sudo netstat -tulpn | grep -E '3000|8000|5432|6379'

# Restart services
./deploy.sh restart
```

#### Database Connection Errors

```bash
# Check PostgreSQL status
./health-check.sh database

# View PostgreSQL logs
./logs.sh postgres 200

# Restart PostgreSQL
docker-compose -f docker-compose.prod.yml restart postgres
```

#### Out of Memory

```bash
# Check memory usage
free -h
docker stats

# Reduce worker count in .env.production
BACKEND_WORKERS=4
POSTGRES_MAX_CONNECTIONS=100

# Restart services
./deploy.sh restart
```

#### Disk Space Issues

```bash
# Check disk usage
df -h

# Clean up Docker
docker system prune -a

# Remove old backups
./backup.sh cleanup 7
```

### Debug Mode

Enable debug logging:

```bash
# Edit .env.production
DEBUG=true
LOG_LEVEL=debug

# Restart services
./deploy.sh restart

# View detailed logs
./logs.sh backend 500 follow
```

### Reset Everything

```bash
# Stop all services
./deploy.sh stop

# Remove all containers and volumes
docker-compose -f docker-compose.prod.yml down -v

# Remove images
docker-compose -f docker-compose.prod.yml down --rmi all

# Start fresh
./deploy.sh deploy
```

## Production Best Practices

### Security

1. **Use strong passwords** for all services
2. **Enable HTTPS** with SSL certificates
3. **Restrict database access** to backend only
4. **Use secrets management** for sensitive data
5. **Regular security updates** for base images

### Performance

1. **Tune PostgreSQL** based on server specs
2. **Configure Redis** memory limits
3. **Use connection pooling** in backend
4. **Enable caching** for frequently accessed data
5. **Monitor resource usage** regularly

### Reliability

1. **Regular backups** (automated daily)
2. **Health checks** for all services
3. **Log monitoring** and alerting
4. **Disaster recovery plan**
5. **Staging environment** for testing

### Scaling

For high-traffic scenarios:

1. **Horizontal scaling**: Run multiple backend instances
2. **Database replication**: Add read replicas
3. **Load balancing**: Use Nginx or cloud load balancer
4. **CDN**: Serve static assets via CDN
5. **Caching**: Increase Redis memory

## Support

For issues and questions:

- Check logs: `./logs.sh errors`
- Run health check: `./health-check.sh`
- Review documentation in `docs/`
- Check GitHub issues

## License

See LICENSE file for details.
