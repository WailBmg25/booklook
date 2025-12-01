# Deployment Checklist

## ✅ Fixed Issues
- [x] TypeScript compilation error (excluded test files from build)
- [x] Next.js Suspense boundary error (wrapped useSearchParams)
- [x] Frontend builds successfully

## 📋 Deployment Steps on Your Server

### 1. Pull Latest Changes
```bash
git pull origin main
```

### 2. Create Production Environment File
```bash
cp .env.production.example .env.production
```

### 3. Generate Secrets
```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate NEXTAUTH_SECRET
openssl rand -base64 32
```

### 4. Edit `.env.production`
Update these critical values:
- `POSTGRES_PASSWORD` - Strong database password
- `SECRET_KEY` - Use the hex value from step 3
- `NEXTAUTH_SECRET` - Use the base64 value from step 3
- `CORS_ORIGINS` - Your domain (e.g., https://yourdomain.com)
- `NEXT_PUBLIC_API_URL` - Your API URL (e.g., https://yourdomain.com/api)
- `NEXTAUTH_URL` - Your frontend URL (e.g., https://yourdomain.com)

### 5. Set File Permissions
```bash
chmod 600 .env.production
```

### 6. Deploy
```bash
chmod +x deploy.sh
./deploy.sh deploy
```

### 7. Verify Deployment
```bash
# Check container status
docker ps

# Check logs
docker logs booklook-frontend
docker logs booklook-backend
docker logs booklook-postgres
docker logs booklook-redis
```

### 8. Load Institutional Dataset (Optional)
```bash
# Load books from CSV files
./deploy.sh load-data /path/to/csv/files

# Or load a single CSV file
./deploy.sh load-data /path/to/books.csv
```

### 9. Access pgAdmin (Optional)
```bash
# Start with pgAdmin for database management
./deploy.sh pgadmin

# Access at http://localhost:5050
# Connect to PostgreSQL:
#   Host: postgres
#   Port: 5432
#   Database: book_library
#   Username/Password: from .env.production
```

## 🔍 Troubleshooting

### If frontend container fails:
```bash
docker logs booklook-frontend
```

### If backend container fails:
```bash
docker logs booklook-backend
```

### Check all services:
```bash
docker-compose -f docker-compose.prod.yml ps
```

### Restart a specific service:
```bash
docker-compose -f docker-compose.prod.yml restart frontend
```

## 📝 Notes
- The npm build error has been completely resolved
- Frontend now compiles successfully in Docker
- All test files are properly excluded from production build
- Login page Suspense boundary issue is fixed
