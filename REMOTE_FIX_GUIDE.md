# Quick Fix Guide for Remote Server

Run these commands on your remote server to fix all issues:

## Step 1: Update Code
```bash
cd ~/Documents/booklook
git pull origin main
```

## Step 2: Fix Environment Variables
```bash
# Create .env file (Docker Compose looks for this by default)
cp .env.production .env

# Verify it has the correct values
grep -E "SECRET_KEY|NEXTAUTH_SECRET|NEXT_PUBLIC_API_URL" .env
```

## Step 3: Rebuild Everything
```bash
# Stop all services
docker-compose -f docker-compose.prod.yml down

# Remove old images to force rebuild
docker rmi booklook-backend booklook-frontend

# Rebuild and start (this will use .env automatically)
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services to start
sleep 20
```

## Step 4: Verify
```bash
# Check all containers are running
docker-compose -f docker-compose.prod.yml ps

# Check backend logs for errors
docker-compose -f docker-compose.prod.yml logs backend | tail -20

# Check frontend logs
docker-compose -f docker-compose.prod.yml logs frontend | tail -20

# Test API
curl https://craig-unmarkable-bambi.ngrok-free.dev/api/v1/books?page=1&page_size=1
```

## Expected Results
- No more "variable is not set" warnings
- Backend should return book data without 500 errors
- Frontend should load (NextAuth 404 is separate issue)

## If Still Having Issues

### Backend 500 Error
```bash
# Check detailed backend logs
docker-compose -f docker-compose.prod.yml logs backend | grep -A 10 "ValidationError"
```

### Frontend Issues
```bash
# Rebuild frontend only
docker-compose -f docker-compose.prod.yml stop frontend
docker rmi booklook-frontend
docker-compose -f docker-compose.prod.yml up -d --build frontend
```

### Environment Variable Issues
```bash
# Verify env vars are loaded in containers
docker-compose -f docker-compose.prod.yml exec backend env | grep SECRET_KEY
docker-compose -f docker-compose.prod.yml exec frontend env | grep NEXT_PUBLIC_API_URL
```
