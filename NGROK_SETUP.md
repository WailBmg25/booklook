# BookLook ngrok Deployment Guide

This guide explains how to deploy BookLook using a single ngrok tunnel with nginx as a reverse proxy.

## Architecture

```
Internet → ngrok (port 80) → nginx → frontend (port 3000)
                                   → backend (port 8000)
```

All traffic comes through one ngrok tunnel on port 80, and nginx routes:
- `/api/*` requests to the backend
- Everything else to the frontend

## Quick Start

### 1. Configure Environment

Edit `.env.production` and update your ngrok URL:

```bash
# Replace with your actual ngrok URL
CORS_ORIGINS=https://your-ngrok-url.ngrok-free.dev
NEXT_PUBLIC_API_URL=https://your-ngrok-url.ngrok-free.dev/api
NEXTAUTH_URL=https://your-ngrok-url.ngrok-free.dev
```

### 2. Deploy Services

```bash
./deploy-ngrok.sh
```

This will:
- Stop existing containers
- Build and start all services (postgres, redis, backend, frontend, nginx)
- Check health status

### 3. Start ngrok Tunnel

In a separate terminal:

```bash
ngrok http 80
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok-free.app`)

### 4. Update Configuration with ngrok URL

Update `.env.production` with your actual ngrok URL:

```bash
CORS_ORIGINS=https://abc123.ngrok-free.app
NEXT_PUBLIC_API_URL=https://abc123.ngrok-free.app/api
NEXTAUTH_URL=https://abc123.ngrok-free.app
```

### 5. Restart Frontend

```bash
docker-compose -f docker-compose.prod.yml restart frontend
```

### 6. Access Your Application

Open your ngrok URL in a browser: `https://abc123.ngrok-free.app`

## How It Works

### Request Flow

1. **Frontend Request**: User visits `https://your-ngrok.app`
   - ngrok → nginx:80 → frontend:3000
   
2. **API Request**: Frontend calls `https://your-ngrok.app/api/v1/books`
   - Browser → ngrok → nginx:80 → backend:8000
   - Response flows back the same way

### Why This Works

- **Single ngrok tunnel**: Only need one free ngrok tunnel on port 80
- **nginx routing**: Intelligently routes requests to frontend or backend
- **No CORS issues**: All requests appear to come from the same origin
- **Docker networking**: Backend and frontend communicate internally via Docker network

## Troubleshooting

### Backend Connection Refused

**Problem**: `ERR_CONNECTION_REFUSED` when calling API

**Solution**: Make sure `NEXT_PUBLIC_API_URL` uses your ngrok URL + `/api`:
```bash
NEXT_PUBLIC_API_URL=https://your-ngrok-url.ngrok-free.dev/api
```

### CORS Errors

**Problem**: CORS policy blocking requests

**Solution**: Add your ngrok URL to `CORS_ORIGINS` in `.env.production`:
```bash
CORS_ORIGINS=https://your-ngrok-url.ngrok-free.dev
```

Then restart backend:
```bash
docker-compose -f docker-compose.prod.yml restart backend
```

### NextAuth Errors

**Problem**: `UntrustedHost` or authentication errors

**Solution**: Ensure these are set in `.env.production`:
```bash
NEXTAUTH_URL=https://your-ngrok-url.ngrok-free.dev
AUTH_TRUST_HOST=true
```

### ngrok URL Changed

**Problem**: ngrok gives you a new URL each time (free tier)

**Solution**: Each time you restart ngrok:
1. Update `.env.production` with new URL
2. Restart frontend: `docker-compose -f docker-compose.prod.yml restart frontend`
3. Restart backend: `docker-compose -f docker-compose.prod.yml restart backend`

## Useful Commands

```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service logs
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f nginx

# Restart a service
docker-compose -f docker-compose.prod.yml restart frontend

# Stop all services
docker-compose -f docker-compose.prod.yml down

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build
```

## Port Reference

- **80**: nginx (expose to ngrok)
- **3000**: frontend (internal only)
- **8000**: backend (internal only)
- **5432**: postgres (internal only)
- **6379**: redis (internal only)
- **5050**: pgadmin (localhost only)

## Security Notes

- Backend is NOT directly exposed (bound to 127.0.0.1)
- All external traffic goes through nginx
- pgAdmin only accessible from localhost
- Use strong passwords in production
- Consider using ngrok authentication for additional security
