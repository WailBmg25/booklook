# Remote Server Deployment with ngrok

This guide is for deploying BookLook on a remote server with ngrok access.

## Prerequisites on Remote Server

- Docker and Docker Compose installed
- Git installed
- ngrok installed and authenticated

## Initial Setup (First Time)

### 1. Clone/Pull Repository

```bash
cd /path/to/your/project
git pull origin main
```

### 2. Create Environment File

```bash
# Copy the example file
cp .env.production.example .env.production

# Edit with your settings
nano .env.production
```

**Important Settings to Configure:**

```bash
# Database (use strong passwords!)
POSTGRES_PASSWORD=your-strong-password-here

# Backend
SECRET_KEY=your-secret-key-here  # Generate with: openssl rand -hex 32

# Frontend - WILL UPDATE AFTER NGROK STARTS
NEXT_PUBLIC_API_URL=https://your-ngrok-url.ngrok-free.dev/api
NEXTAUTH_URL=https://your-ngrok-url.ngrok-free.dev
NEXTAUTH_SECRET=your-nextauth-secret  # Generate with: openssl rand -base64 32
AUTH_TRUST_HOST=true

# CORS - WILL UPDATE AFTER NGROK STARTS
CORS_ORIGINS=https://your-ngrok-url.ngrok-free.dev
```

### 3. Deploy Services

```bash
# Make script executable
chmod +x deploy-ngrok.sh

# Deploy
./deploy-ngrok.sh
```

### 4. Start ngrok

In a separate terminal or screen session:

```bash
# Start ngrok on port 80
ngrok http 80

# Or use screen to keep it running
screen -S ngrok
ngrok http 80
# Press Ctrl+A then D to detach
```

Copy the HTTPS URL from ngrok (e.g., `https://abc123.ngrok-free.app`)

### 5. Update Configuration with ngrok URL

```bash
# Edit .env.production
nano .env.production

# Update these lines with your actual ngrok URL:
CORS_ORIGINS=https://abc123.ngrok-free.app
NEXT_PUBLIC_API_URL=https://abc123.ngrok-free.app/api
NEXTAUTH_URL=https://abc123.ngrok-free.app
```

### 6. Restart Services

```bash
# Restart frontend and backend to pick up new URLs
docker-compose -f docker-compose.prod.yml restart frontend backend
```

### 7. Access Your Application

Open your ngrok URL in a browser: `https://abc123.ngrok-free.app`

## Updating Deployment (After Git Pull)

When you pull new changes from GitHub:

```bash
# 1. Pull latest changes
git pull origin main

# 2. Rebuild and restart services
docker-compose -f docker-compose.prod.yml up -d --build

# 3. Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

## Managing ngrok URL Changes

ngrok free tier gives you a new URL each time you restart. When this happens:

```bash
# 1. Get new ngrok URL
# 2. Update .env.production with new URL
nano .env.production

# 3. Restart services
docker-compose -f docker-compose.prod.yml restart frontend backend
```

## Using Screen for Persistent Sessions

To keep ngrok running after you disconnect:

```bash
# Create new screen session
screen -S ngrok

# Start ngrok
ngrok http 80

# Detach from screen: Press Ctrl+A then D

# List screens
screen -ls

# Reattach to screen
screen -r ngrok

# Kill screen session
screen -X -S ngrok quit
```

## Useful Commands

```bash
# View all service logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service
docker-compose -f docker-compose.prod.yml logs -f nginx
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f backend

# Check service status
docker-compose -f docker-compose.prod.yml ps

# Restart a service
docker-compose -f docker-compose.prod.yml restart frontend

# Stop all services
docker-compose -f docker-compose.prod.yml down

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build

# View nginx access logs
docker-compose -f docker-compose.prod.yml exec nginx tail -f /var/log/nginx/access.log

# View nginx error logs
docker-compose -f docker-compose.prod.yml exec nginx tail -f /var/log/nginx/error.log
```

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs

# Check if ports are in use
sudo netstat -tulpn | grep -E ':(80|3000|8000|5432|6379)'

# Remove old containers and volumes
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d --build
```

### Can't Access Through ngrok

1. Verify ngrok is running: `curl http://localhost:80`
2. Check nginx logs: `docker-compose -f docker-compose.prod.yml logs nginx`
3. Verify CORS_ORIGINS matches your ngrok URL
4. Restart services after changing .env.production

### API Calls Failing

1. Check NEXT_PUBLIC_API_URL ends with `/api`
2. Verify CORS_ORIGINS in .env.production
3. Check backend logs: `docker-compose -f docker-compose.prod.yml logs backend`
4. Test backend directly: `curl http://localhost:80/api/health`

### Database Connection Issues

```bash
# Check postgres is running
docker-compose -f docker-compose.prod.yml ps postgres

# Check postgres logs
docker-compose -f docker-compose.prod.yml logs postgres

# Connect to postgres
docker-compose -f docker-compose.prod.yml exec postgres psql -U bookuser -d book_library
```

## Security Recommendations

1. **Use strong passwords** in .env.production
2. **Never commit** .env.production to git
3. **Restrict file permissions**: `chmod 600 .env.production`
4. **Use ngrok authentication** for additional security
5. **Monitor logs** regularly for suspicious activity
6. **Keep Docker images updated**: `docker-compose pull`

## Architecture

```
Internet
   ↓
ngrok (port 80)
   ↓
nginx:80 (reverse proxy)
   ├─→ /api/* → backend:8000 (FastAPI)
   └─→ /* → frontend:3000 (Next.js)
```

All services communicate internally via Docker network. Only nginx is exposed to ngrok.
