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
a889bb1555a6ffe633b2108a69fb4b6c34c6bb87e1bb0c132fa72d43ec612857
# Generate NEXTAUTH_SECRET (copy the output)
openssl rand -base64 32
d3kr/97paZ51FkOg74+F1rYmg/fSikPyYpD5emQ8Y8Q=
# Generate POSTGRES_PASSWORD (copy the output)
openssl rand -base64 32
IzWVnclndy4TsYYZST58kepbox7yaOXEJRWzTg23eeA=
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

**4. URLs (for IP-based access):**

First, find your machine's IP address:
```bash
# Get your IP address
ip addr show | grep "inet " | grep -v 127.0.0.1
# Or simpler:
hostname -I | awk '{print $1}'
```

Let's say your IP is `192.168.1.100` (replace with your actual IP):

```bash
# Find these lines:
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
NEXTAUTH_URL=https://yourdomain.com
NEXT_PUBLIC_API_URL=https://yourdomain.com/api

# Replace with your IP address:
CORS_ORIGINS=http://192.168.1.100:3000,http://localhost:3000
NEXTAUTH_URL=http://192.168.1.100:3000
NEXT_PUBLIC_API_URL=http://192.168.1.100:8000
```

**Important:** Replace `192.168.1.100` with YOUR actual IP address!

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

### From the Same Machine:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### From Any Device on Your Network (or Internet):

Replace `192.168.1.100` with your actual IP address:

- **Frontend**: http://192.168.1.100:3000
- **Backend API**: http://192.168.1.100:8000
- **API Documentation**: http://192.168.1.100:8000/docs

### To Access from Internet (Outside Your Network):

You need to configure your router to forward ports:

1. **Find your public IP**: Go to https://whatismyipaddress.com/
2. **Configure port forwarding** on your router:
   - Forward port `3000` → Your machine's local IP (192.168.1.100)
   - Forward port `8000` → Your machine's local IP (192.168.1.100)
3. **Access using public IP**: http://YOUR_PUBLIC_IP:3000

**Security Warning:** Opening ports to the internet without SSL is not secure. Use this only for testing. For production, get a domain and use SSL.

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

## Step 8: When You Buy a Domain (Optional)

Once you have a domain (e.g., `mybooklook.com`), follow these steps:

### 1. Point Domain to Your IP

In your domain registrar (Namecheap, GoDaddy, etc.), add DNS records:

```
Type: A Record
Name: @
Value: YOUR_PUBLIC_IP (from whatismyipaddress.com)

Type: A Record  
Name: www
Value: YOUR_PUBLIC_IP
```

Wait 1-24 hours for DNS propagation.

### 2. Update Configuration

```bash
# Stop services
./deploy.sh stop

# Edit environment file
nano .env.production

# Update these lines (replace mybooklook.com with your domain):
CORS_ORIGINS=https://mybooklook.com,https://www.mybooklook.com,http://mybooklook.com,http://www.mybooklook.com
NEXTAUTH_URL=https://mybooklook.com
NEXT_PUBLIC_API_URL=https://mybooklook.com/api
```

### 3. Get Free SSL Certificate

```bash
# Install certbot
sudo apt-get install -y certbot

# Stop services temporarily
./deploy.sh stop

# Get certificate (replace with your domain and email)
sudo certbot certonly --standalone \
    -d mybooklook.com \
    -d www.mybooklook.com \
    --email your@email.com \
    --agree-tos \
    --non-interactive

# Copy certificates
sudo mkdir -p docker/nginx/ssl
sudo cp /etc/letsencrypt/live/mybooklook.com/fullchain.pem docker/nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/mybooklook.com/privkey.pem docker/nginx/ssl/key.pem
sudo chmod 644 docker/nginx/ssl/cert.pem
sudo chmod 600 docker/nginx/ssl/key.pem
```

### 4. Update Nginx Configuration

```bash
nano docker/nginx/nginx.conf
```

Find the commented HTTPS section and uncomment it, then update the domain:

```nginx
server {
    listen 443 ssl http2;
    server_name mybooklook.com www.mybooklook.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # ... rest of configuration
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name mybooklook.com www.mybooklook.com;
    return 301 https://$server_name$request_uri;
}
```

### 5. Deploy with Nginx

```bash
# Start with nginx profile
docker-compose -f docker-compose.prod.yml --profile with-nginx up -d

# Check status
./deploy.sh status
./health-check.sh
```

### 6. Set Up Auto-Renewal for SSL

```bash
# Test renewal
sudo certbot renew --dry-run

# Add to crontab for auto-renewal
sudo crontab -e

# Add this line (renews every Monday at 2 AM):
0 2 * * 1 certbot renew --quiet && cp /etc/letsencrypt/live/mybooklook.com/*.pem /home/$USER/booklook/docker/nginx/ssl/ && docker-compose -f /home/$USER/booklook/docker-compose.prod.yml restart nginx
```

### 7. Update Router Port Forwarding

Change port forwarding to use standard ports:
- Forward port `80` → Your machine's local IP
- Forward port `443` → Your machine's local IP
- Remove port `3000` and `8000` forwarding (Nginx handles this now)

### 8. Access Your Site

Now you can access your site at:
- https://mybooklook.com (secure!)
- https://www.mybooklook.com

**Note:** Everything still runs on one machine. The domain just points to your IP address, and Nginx routes traffic to the correct services (frontend on port 3000, backend on port 8000).

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

## Deployment Scenarios Summary

### Scenario 1: Local Testing Only
- **URLs**: `localhost:3000` and `localhost:8000`
- **Access**: Only from the same machine
- **SSL**: Not needed
- **Use case**: Development and testing

### Scenario 2: Network Access (Current Setup)
- **URLs**: `http://YOUR_IP:3000` and `http://YOUR_IP:8000`
- **Access**: From any device on your network
- **SSL**: Not needed (but not secure for internet)
- **Use case**: Testing from multiple devices, showing to friends

### Scenario 3: Internet Access (Port Forwarding)
- **URLs**: `http://YOUR_PUBLIC_IP:3000` and `http://YOUR_PUBLIC_IP:8000`
- **Access**: From anywhere in the world
- **SSL**: Recommended but not required
- **Use case**: Public testing, temporary deployment
- **Setup**: Configure router port forwarding

### Scenario 4: Production with Domain
- **URLs**: `https://yourdomain.com`
- **Access**: From anywhere in the world
- **SSL**: Required (free with Let's Encrypt)
- **Use case**: Production deployment
- **Setup**: Buy domain, configure DNS, get SSL certificate, use Nginx

**Current Guide**: Covers Scenario 2 & 3, with instructions for upgrading to Scenario 4 when ready.

---

**That's it! You now have BookLook running on your Kali Linux system.** 🎉

**Quick Access:**
- Same machine: http://localhost:3000
- Your network: http://YOUR_IP:3000
- Internet: http://YOUR_PUBLIC_IP:3000 (after port forwarding)
