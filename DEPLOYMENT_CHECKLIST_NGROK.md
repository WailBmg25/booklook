# ngrok Deployment Checklist

Use this checklist when deploying to your remote server.

## Before Pushing to GitHub

- [x] `.env.production` is in `.gitignore` (already done)
- [x] `frontend/.env.local` is in `.gitignore` (already done)
- [x] Updated `.env.production.example` with ngrok instructions
- [x] Created `deploy-ngrok.sh` script
- [x] Created `NGROK_SETUP.md` guide
- [x] Created `REMOTE_DEPLOYMENT.md` guide
- [x] Updated `docker-compose.prod.yml` to expose nginx

## On Remote Server (After Git Pull)

### 1. Initial Setup
```bash
# Pull latest code
git pull origin main

# Create environment file
cp .env.production.example .env.production

# Generate secrets
openssl rand -hex 32  # For SECRET_KEY
openssl rand -base64 32  # For NEXTAUTH_SECRET

# Edit .env.production with your secrets
nano .env.production
```

### 2. Deploy Services
```bash
# Make script executable
chmod +x deploy-ngrok.sh

# Deploy
./deploy-ngrok.sh
```

### 3. Start ngrok
```bash
# In a screen session (recommended)
screen -S ngrok
ngrok http 80
# Ctrl+A then D to detach

# Copy the HTTPS URL (e.g., https://abc123.ngrok-free.app)
```

### 4. Update Configuration
```bash
# Edit .env.production
nano .env.production

# Update these three lines with your ngrok URL:
# CORS_ORIGINS=https://abc123.ngrok-free.app
# NEXT_PUBLIC_API_URL=https://abc123.ngrok-free.app/api
# NEXTAUTH_URL=https://abc123.ngrok-free.app
```

### 5. Restart Services
```bash
docker-compose -f docker-compose.prod.yml restart frontend backend
```

### 6. Verify
```bash
# Check all services are running
docker-compose -f docker-compose.prod.yml ps

# Test health endpoint
curl http://localhost:80/health

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 7. Access Application
- Open your ngrok URL in browser
- Test login/registration
- Test API calls (check browser console for errors)

## Common Issues & Quick Fixes

### Issue: ERR_CONNECTION_REFUSED
**Fix:** 
```bash
# Verify NEXT_PUBLIC_API_URL ends with /api
grep NEXT_PUBLIC_API_URL .env.production
# Should show: NEXT_PUBLIC_API_URL=https://your-url.ngrok-free.app/api
```

### Issue: CORS Errors
**Fix:**
```bash
# Verify CORS_ORIGINS matches ngrok URL
grep CORS_ORIGINS .env.production
# Should show: CORS_ORIGINS=https://your-url.ngrok-free.app

# Restart backend
docker-compose -f docker-compose.prod.yml restart backend
```

### Issue: NextAuth Errors
**Fix:**
```bash
# Verify AUTH_TRUST_HOST is set
grep AUTH_TRUST_HOST .env.production
# Should show: AUTH_TRUST_HOST=true

# Restart frontend
docker-compose -f docker-compose.prod.yml restart frontend
```

### Issue: ngrok URL Changed
**Fix:**
```bash
# 1. Update .env.production with new URL
nano .env.production

# 2. Restart services
docker-compose -f docker-compose.prod.yml restart frontend backend
```

## Files to Commit to GitHub

✅ Commit these:
- `docker-compose.prod.yml` (updated)
- `.env.production.example` (updated)
- `deploy-ngrok.sh` (new)
- `NGROK_SETUP.md` (new)
- `REMOTE_DEPLOYMENT.md` (new)
- `DEPLOYMENT_CHECKLIST_NGROK.md` (this file)

❌ DO NOT commit:
- `.env.production` (contains secrets)
- `frontend/.env.local` (contains secrets)
- Any files with actual passwords or keys

## Git Commands

```bash
# Check what will be committed
git status

# Add new files
git add deploy-ngrok.sh NGROK_SETUP.md REMOTE_DEPLOYMENT.md DEPLOYMENT_CHECKLIST_NGROK.md
git add docker-compose.prod.yml .env.production.example

# Commit
git commit -m "Add ngrok deployment configuration with nginx reverse proxy"

# Push to GitHub
git push origin main
```

## On Remote Server After Push

```bash
# Pull changes
git pull origin main

# Follow steps in REMOTE_DEPLOYMENT.md
```
