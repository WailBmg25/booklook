#!/bin/bash

echo "🚀 Starting BookLook Application..."
echo ""

# Start Docker services (PostgreSQL and Redis)
echo "📦 Starting Docker services (PostgreSQL & Redis)..."
cd docker && docker-compose up -d postgres redis
cd ..

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 3

# Start Backend (FastAPI)
echo "🔧 Starting Backend (FastAPI)..."
source ~/anaconda3/etc/profile.d/conda.sh
conda activate booklook
python main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Start Frontend (Next.js)
echo "🎨 Starting Frontend (Next.js)..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ BookLook is starting up!"
echo ""
echo "📍 Access Points:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://127.0.0.1:8000"
echo "   API Docs:  http://127.0.0.1:8000/docs"
echo "   pgAdmin:   http://localhost:5050"
echo ""
echo "🔐 Database Access:"
echo "   Host:      localhost"
echo "   Port:      5432"
echo "   Database:  book_library"
echo "   Username:  bookuser"
echo "   Password:  bookpass123"
echo ""
echo "🔐 pgAdmin Access:"
echo "   URL:       http://localhost:5050"
echo "   Email:     admin@booklib.com"
echo "   Password:  admin123"
echo ""
echo "👤 Test Account:"
echo "   Email:     final_test@example.com"
echo "   Password:  Test1234"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for user interrupt
wait
