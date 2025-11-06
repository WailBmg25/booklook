# 🚀 BookLook - Quick Start Guide

## ✅ Everything is Running!

Your BookLook application is now running with all services started.

---

## 📍 Access Points

### **Frontend (User Interface)**
- **URL:** http://localhost:3000
- **Description:** Main application interface for browsing books, reading, and managing favorites

### **Backend API**
- **URL:** http://127.0.0.1:8000
- **API Docs:** http://127.0.0.1:8000/docs (Interactive Swagger UI)
- **Description:** FastAPI backend with all endpoints

---

## 🔐 Database Access

### **PostgreSQL Database**
- **Host:** localhost
- **Port:** 5432
- **Database:** book_library
- **Username:** bookuser
- **Password:** bookpass123

### **Connect via Command Line:**
```bash
psql -h localhost -U bookuser -d book_library
# Password: bookpass123
```

### **Connect via pgAdmin (Web Interface)**
- **URL:** http://localhost:5050
- **Email:** admin@booklib.com
- **Password:** admin123

**To add server in pgAdmin:**
1. Open http://localhost:5050
2. Login with credentials above
3. Right-click "Servers" → "Register" → "Server"
4. General tab: Name = "BookLook"
5. Connection tab:
   - Host: postgres (or host.docker.internal)
   - Port: 5432
   - Database: book_library
   - Username: bookuser
   - Password: bookpass123

---

## 👤 Test Accounts

### **Test User Account**
- **Email:** final_test@example.com
- **Password:** Test1234

### **Your Account**
- **Email:** wl.boumagouda@gmail.com
- **Password:** (the password you set during registration)

---

## 🎯 Features to Test

1. **Browse Books**
   - Go to http://localhost:3000
   - Search for books (try "P", "Python", "Jane")
   - Filter by genre, author, rating
   - Sort books

2. **Book Details**
   - Click on any book
   - View details, reviews, ratings
   - Add to favorites (heart icon)
   - Click "Read" to start reading

3. **Reading Interface**
   - Smooth scrolling text
   - Progress tracking
   - Font size adjustment
   - Light/dark theme toggle

4. **Reviews**
   - Write reviews with ratings
   - View other users' reviews
   - Delete your own reviews

5. **Favorites**
   - Click heart icons to add/remove favorites
   - View all favorites at http://localhost:3000/favorites

---

## 🛠️ Starting/Stopping Services

### **Start Everything (One Command)**
```bash
./start.sh
```

### **Stop Everything**
Press `Ctrl+C` in the terminal where services are running

Or manually:
```bash
# Stop Docker services
cd docker && docker-compose down

# Stop backend/frontend
# Press Ctrl+C in their respective terminals
```

### **Restart Individual Services**

**Backend only:**
```bash
source ~/anaconda3/etc/profile.d/conda.sh
conda activate booklook
python main.py
```

**Frontend only:**
```bash
cd frontend
npm run dev
```

**Docker services only:**
```bash
cd docker
docker-compose up -d postgres redis
```

---

## 📊 Sample Data

The database contains:
- **5 Books** with different genres
- **3 Authors** (Bob Johnson, Jane Smith, John Doe)
- **4 Genres** (Fantasy, Fiction, Programming, Science Fiction)
- **Multiple Reviews** with ratings

---

## 🔧 Troubleshooting

### **Port Already in Use**
If you get port errors:
```bash
# Check what's using the port
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# Kill the process
kill -9 <PID>
```

### **Database Connection Issues**
```bash
# Restart PostgreSQL
cd docker
docker-compose restart postgres
```

### **Redis Issues**
```bash
# Restart Redis
cd docker
docker-compose restart redis

# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL
```

### **Session Expired**
- Just log in again
- Sessions expire after 24 hours

---

## 📁 Project Structure

```
bookbook/
├── src/                    # Backend (FastAPI)
│   ├── models/            # Database models
│   ├── controllers/       # Business logic
│   ├── repositories/      # Data access
│   ├── routes/            # API endpoints
│   └── helpers/           # Utilities
├── frontend/              # Frontend (Next.js)
│   └── src/
│       ├── app/          # Pages
│       ├── components/   # React components
│       └── lib/          # API clients
├── docker/               # Docker services
│   └── docker-compose.yml
└── start.sh             # Startup script
```

---

## 🎉 Enjoy BookLook!

Everything is set up and running. Start exploring books, reading, and managing your library!

For issues or questions, check the logs:
- Backend logs: In the terminal where `python main.py` is running
- Frontend logs: In the terminal where `npm run dev` is running
- Docker logs: `cd docker && docker-compose logs -f`
