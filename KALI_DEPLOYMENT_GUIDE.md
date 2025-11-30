# BookLook Deployment Guide for Kali Linux

This is a simple, step-by-step guide to deploy BookLook on Kali Linux.

## Prerequisites

- Kali Linux installed
- Internet connection
- At least 8GB RAM and 50GB free disk space

---

## Step 1: Install Docker

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
sudo apt-get install -y docker.io docker-compose

# Start Docker service
sudo systemctl enable docker
sudo systemctl start docker

# Add your user to docker group
sudo usermod -aG docker $USER

# Activate the group (choose one):
# Option A: Use newgrp (works immediately in current terminal)
newgrp docker

# Option B: Logout and login again (more reliable)
# Just close terminal and open a new one

# Verify Docker works
docker run hello-world
```

If you see "Hello from Docker!" message, Docker is working correctly.

---

## Step 2: Get the BookLook Code

```bash
# Navigate to where you want to install
cd ~

# Clone the repository (replace with your actual repo URL)
git clone <your-repository-url> booklook

# Enter the directory
cd booklook
```

---

## Step 3: Generate Security Keys

You need to generate 3 secret keys. Run these commands and **save the output**:

```bash
# Generate SECRET_KEY (copy the output)
openssl rand -hex 32

# Generate NEXTAUTH_SECRET (copy the output)
openssl rand -base64 32

# Generate POSTGRES_PASSWORD (copy the output)
openssl rand -base64 32
```

**Write these down! You'll need them in the next step.**

---

## Step 4: Configure Environment

```bash
# Copy the example configuration file
cp .env.production.example .env.production

# Open the file for editing
nano .env.production
```

Now edit these values in the file:

### Find and Replace These Lines:

**1. Database Password:**
```bash
# Find this line:
POSTGRES_PASSWORD=CHANGE_ME_STRONG_PASSWORD_HERE

# Replace with the password you generated:
POSTGRES_PASSWORD=<paste-your-generated-password>
```

**2. Backend Secret Key:**
```bash
# Find this line:
SECRET_KEY=CHANGE_ME_GENERATE_RANDOM_SECRET_KEY_HERE

# Replace with the SECRET_KEY you generated:
SECRET_KEY=<paste-your-secret-key>
```

**3. NextAuth Secret:**
```bash
# Find this line:
NEXTAUTH_SECRET=CHANGE_ME_GENERATE_RANDOM_NEXTAUTH_SECRET_HERE

# Replace with the NEXTAUTH_SECRET you generated:
NEXTAUTH_SECRET=<paste-your-nextauth-secret>
```

**4. URLs (for local testing):**
```bash
# Find these lines:
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
NEXTAUTH_URL=https://yourdomain.com
NEXT_PUBLIC_API_URL=https://yourdomain.com/api

# Replace with localhost:
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
NEXTAUTH_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**5. Adjust Resources (if you have less than 32GB RAM):**

If you have 8GB RAM:
```bash
POSTGRES_SHARED_BUFFERS=2GB
POSTGRES_EFFECTIVE_CACHE_SIZE=6GB
POSTGRES_MAINTENANCE_WORK_MEM=512MB
POSTGRES_WORK_MEM=16MB
BACKEND_WORKERS=2
REDIS_MAX_MEMORY=1gb
```

If you have 16GB RAM:
```bash
POSTGRES_SHARED_BUFFERS=4GB
POSTGRES_EFFECTIVE_CACHE_SIZE=12GB
POSTGRES_MAINTENANCE_WORK_MEM=1GB
POSTGRES_WORK_MEM=32MB
BACKEND_WORKERS=4
REDIS_MAX_MEMORY=2gb
```

**Save and exit:**
- Press `Ctrl + X`
- Press `Y` to confirm
- Press `Enter` to save

---

## Step 5: Deploy BookLook

```bash
# Make deployment script executable
chmod +x deploy.sh

# Deploy the application
./deploy.sh deploy
```

This will:
1. Build Docker images (takes 5-10 minutes)
2. Start all services
3. Run database migrations
4. Check if everything is healthy

**Wait for it to complete.** You'll see messages about building and starting services.

---

## Step 6: Verify Deployment

```bash
# Check if all services are running
docker ps

# You should see 4 containers:
# - booklook-backend-1
# - booklook-frontend-1
# - booklook-postgres-1
# - booklook-redis-1

# Run health check
./health-check.sh full
```

If all checks pass, you're good to go!

---

## Step 7: Access BookLook

Open your web browser and go to:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

---

## Common Commands

### View Logs
```bash
# View all logs
./logs.sh all

# View only errors
./logs.sh errors

# View specific service logs
./logs.sh backend
./logs.sh frontend
./logs.sh postgres
```

### Stop Services
```bash
./deploy.sh stop
```

### Start Services
```bash
./deploy.sh start
```

### Restart Services
```bash
./deploy.sh restart
```

### Check Status
```bash
./deploy.sh status
```

### Create Backup
```bash
./backup.sh full
```

---

## Troubleshooting

### Problem: "Permission denied" when running Docker

**Solution:**
```bash
# Add yourself to docker group again
sudo usermod -aG docker $USER

# Then logout and login, or run:
newgrp docker
```

### Problem: Port already in use

**Solution:**
```bash
# Check what's using the port
sudo netstat -tulpn | grep :3000
sudo netstat -tulpn | grep :8000

# Kill the process or change ports in .env.production
```

### Problem: Services won't start

**Solution:**
```bash
# Check logs for errors
./logs.sh all

# Restart Docker
sudo systemctl restart docker

# Try deploying again
./deploy.sh deploy
```

### Problem: Out of disk space

**Solution:**
```bash
# Check disk space
df -h

# Clean up Docker
docker system prune -a

# Remove old images
docker image prune -a
```

### Problem: Database connection failed

**Solution:**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Restart PostgreSQL
docker-compose -f docker-compose.prod.yml restart postgres

# Check PostgreSQL logs
./logs.sh postgres
```

---

## Creating Your First Admin User

After deployment, you need to create an admin user:

```bash
# Connect to the database
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U bookuser -d book_library

# In the PostgreSQL prompt, run:
INSERT INTO users (email, first_name, last_name, password_hash, is_admin, is_active)
VALUES (
    'admin@booklook.com',
    'Admin',
    'User',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVr/1jrPK',
    true,
    true
);

# Exit PostgreSQL
\q
```

**Default admin credentials:**
- Email: `admin@booklook.com`
- Password: `admin123`

**⚠️ Change this password immediately after first login!**

---

## Next Steps

1. **Change admin password** in the application
2. **Add some books** through the admin interface
3. **Create regular user accounts** for testing
4. **Explore the API** at http://localhost:8000/docs

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `./deploy.sh deploy` | Full deployment |
| `./deploy.sh start` | Start services |
| `./deploy.sh stop` | Stop services |
| `./deploy.sh restart` | Restart services |
| `./deploy.sh status` | Check status |
| `./health-check.sh` | Health check |
| `./logs.sh all` | View all logs |
| `./logs.sh errors` | View errors only |
| `./backup.sh full` | Create backup |
| `docker ps` | List containers |
| `docker stats` | Resource usage |

---

## Getting Help

If you encounter issues:

1. Check the logs: `./logs.sh errors`
2. Run health check: `./health-check.sh`
3. Check Docker status: `docker ps`
4. Review this guide's troubleshooting section

---

**That's it! You now have BookLook running on your Kali Linux system.** 🎉
