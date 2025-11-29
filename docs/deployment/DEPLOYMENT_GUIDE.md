# BookLook Deployment Guide - Local Machine with Domain

## 📋 Overview

This guide covers deploying BookLook on a local machine and making it accessible via a custom domain.

---

## 🖥️ Local Machine Deployment

### Prerequisites

- Ubuntu/Debian Linux (or similar)
- Python 3.13+
- PostgreSQL 15+
- Redis 7+
- Nginx
- Docker & Docker Compose (optional)
- Minimum 16GB RAM (for large dataset)
- Minimum 500GB storage (for 300GB+ dataset)

---

## 📦 Step 1: System Setup

### Install Required Software

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.13
sudo apt install python3.13 python3.13-venv python3-pip -y

# Install PostgreSQL 15
sudo apt install postgresql-15 postgresql-contrib -y

# Install Redis
sudo apt install redis-server -y

# Install Nginx
sudo apt install nginx -y

# Install Docker (optional)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### Configure PostgreSQL

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE booklook;
CREATE USER booklook_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE booklook TO booklook_user;
ALTER DATABASE booklook OWNER TO booklook_user;
\q

# Allow remote connections (if needed)
sudo nano /etc/postgresql/15/main/postgresql.conf
# Change: listen_addresses = '*'

sudo nano /etc/postgresql/15/main/pg_hba.conf
# Add: host all all 0.0.0.0/0 md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Configure Redis

```bash
# Edit Redis config
sudo nano /etc/redis/redis.conf

# Recommended settings:
# maxmemory 2gb
# maxmemory-policy allkeys-lru
# bind 127.0.0.1

# Restart Redis
sudo systemctl restart redis
```

---

## 📂 Step 2: Deploy Application

### Clone Repository

```bash
cd /opt
sudo git clone https://github.com/WailBmg25/booklook.git
sudo chown -R $USER:$USER booklook
cd booklook
```

### Setup Python Environment

```bash
# Using conda (recommended)
conda create -n booklook python=3.13
conda activate booklook
pip install -r src/requirements.txt

# Or using venv
python3.13 -m venv venv
source venv/bin/activate
pip install -r src/requirements.txt
```

### Configure Environment

```bash
# Copy environment template
cp src/.env.example src/.env

# Edit configuration
nano src/.env
```

**src/.env:**
```bash
# Database
POSTGRES_USER=booklook_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=booklook

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Application
DEBUG=False
CORS_ORIGINS=["http://localhost:3000","http://yourdomain.com"]

# Pagination
DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100
```

### Run Database Migrations

```bash
cd src
source ~/anaconda3/etc/profile.d/conda.sh
conda activate booklook
alembic upgrade head
```

---

## 📊 Step 3: Load Dataset

### Prepare Your CSV Files

Your CSV files should have these columns:
- `isbn` - Book ISBN
- `lccn` - Library of Congress Control Number
- `title` - Book title
- `author` - Author name
- `text` - JSON array of page content
- `publication_date` - Publication date
- `cover_url` - Cover image URL

**Example CSV:**
```csv
isbn,lccn,title,author,text,publication_date,cover_url
"978-0-123456-78-9","12345678","Python Programming","John Doe","[""Page 1 content..."", ""Page 2 content...""]","2023-01-15","https://example.com/cover.jpg"
```

### Run Import Script

```bash
# Single CSV file
python load_institutional_dataset.py /path/to/books.csv

# Directory of CSV files
python load_institutional_dataset.py /path/to/csv/directory

# With options
python load_institutional_dataset.py /path/to/csv/directory \
  --batch-size 100 \
  --skip-existing

# Monitor progress
tail -f dataset_import.log
```

### Import Options

- `--batch-size 100` - Process 100 books at a time (adjust based on RAM)
- `--skip-existing` - Skip books that already exist (useful for resuming)

### Expected Performance

- **Small dataset** (1,000 books): ~2-5 minutes
- **Medium dataset** (10,000 books): ~20-30 minutes
- **Large dataset** (100,000 books): ~3-5 hours
- **Very large dataset** (1,000,000 books): ~30-50 hours

---

## 🚀 Step 4: Start Backend Server

### Using Systemd (Production)

Create service file:

```bash
sudo nano /etc/systemd/system/booklook.service
```

**booklook.service:**
```ini
[Unit]
Description=BookLook FastAPI Application
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=your_username
WorkingDirectory=/opt/booklook
Environment="PATH=/home/your_username/anaconda3/envs/booklook/bin"
ExecStart=/home/your_username/anaconda3/envs/booklook/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable booklook
sudo systemctl start booklook
sudo systemctl status booklook
```

### Using Screen (Development)

```bash
# Start in screen session
screen -S booklook
conda activate booklook
python main.py

# Detach: Ctrl+A, then D
# Reattach: screen -r booklook
```

---

## 🌐 Step 5: Setup Nginx Reverse Proxy

### Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/booklook
```

**booklook nginx config:**
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # API Backend
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeout for large requests
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
    
    # Frontend (if using Next.js)
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static files
    location /static/ {
        alias /opt/booklook/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # File upload size limit
    client_max_body_size 100M;
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/booklook /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔒 Step 6: Setup SSL (HTTPS)

### Using Let's Encrypt (Free)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal is configured automatically
# Test renewal:
sudo certbot renew --dry-run
```

---

## 🌍 Step 7: Domain Configuration

### Option A: Using Your Own Domain

1. **Purchase domain** from registrar (Namecheap, GoDaddy, etc.)

2. **Configure DNS records:**
   ```
   Type: A
   Name: @
   Value: YOUR_LOCAL_MACHINE_IP
   TTL: 3600
   
   Type: A
   Name: www
   Value: YOUR_LOCAL_MACHINE_IP
   TTL: 3600
   ```

3. **Get your local machine's public IP:**
   ```bash
   curl ifconfig.me
   ```

4. **Configure port forwarding on your router:**
   - Forward port 80 (HTTP) to your machine
   - Forward port 443 (HTTPS) to your machine

### Option B: Using Dynamic DNS (for home network)

If your IP changes frequently:

```bash
# Install ddclient
sudo apt install ddclient -y

# Configure for your DNS provider
sudo nano /etc/ddclient.conf
```

**Example ddclient.conf:**
```
protocol=dyndns2
use=web
server=domains.google.com
login=your_username
password='your_password'
yourdomain.com
```

### Option C: Using Cloudflare Tunnel (Recommended for Home)

No port forwarding needed!

```bash
# Install cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Login to Cloudflare
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create booklook

# Configure tunnel
nano ~/.cloudflared/config.yml
```

**config.yml:**
```yaml
tunnel: YOUR_TUNNEL_ID
credentials-file: /home/your_username/.cloudflared/YOUR_TUNNEL_ID.json

ingress:
  - hostname: yourdomain.com
    service: http://localhost:80
  - service: http_status:404
```

```bash
# Run tunnel
cloudflared tunnel run booklook

# Or as service
sudo cloudflared service install
sudo systemctl start cloudflared
```

---

## 🎨 Step 8: Deploy Frontend

### Build Next.js Frontend

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Start production server
npm start

# Or use PM2 for process management
npm install -g pm2
pm2 start npm --name "booklook-frontend" -- start
pm2 save
pm2 startup
```

---

## 🔧 Step 9: Performance Optimization

### PostgreSQL Tuning

```bash
sudo nano /etc/postgresql/15/main/postgresql.conf
```

**Recommended settings for 16GB RAM:**
```ini
shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 20MB
min_wal_size = 1GB
max_wal_size = 4GB
max_worker_processes = 8
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
```

```bash
sudo systemctl restart postgresql
```

### Redis Tuning

```bash
sudo nano /etc/redis/redis.conf
```

**Recommended settings:**
```ini
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

```bash
sudo systemctl restart redis
```

---

## 📊 Step 10: Monitoring

### Setup Monitoring

```bash
# Install monitoring tools
sudo apt install htop iotop nethogs -y

# Monitor system resources
htop

# Monitor database
sudo -u postgres psql -d booklook -c "SELECT * FROM pg_stat_activity;"

# Monitor logs
tail -f dataset_import.log
journalctl -u booklook -f
tail -f /var/log/nginx/access.log
```

### Health Check Endpoint

The API includes a health check:
```bash
curl http://localhost:8000/
# Should return: {"message": "Welcome to BookLook API"}
```

---

## 🔐 Step 11: Security

### Firewall Configuration

```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check status
sudo ufw status
```

### Secure PostgreSQL

```bash
# Edit pg_hba.conf
sudo nano /etc/postgresql/15/main/pg_hba.conf

# Use md5 authentication
# local   all   all   md5
# host    all   all   127.0.0.1/32   md5
```

### Secure Redis

```bash
# Set password
sudo nano /etc/redis/redis.conf
# Add: requirepass your_redis_password

# Update your .env
REDIS_PASSWORD=your_redis_password
```

---

## 📝 Step 12: Backup Strategy

### Database Backup Script

Create `backup_database.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/booklook"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U booklook_user -h localhost booklook | gzip > $BACKUP_DIR/booklook_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "booklook_*.sql.gz" -mtime +7 -delete

echo "Backup completed: booklook_$DATE.sql.gz"
```

```bash
chmod +x backup_database.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /opt/booklook/backup_database.sh
```

---

## 🌐 Step 13: Domain Setup

### Get Your Public IP

```bash
# Get public IP
curl ifconfig.me

# Example output: 203.0.113.45
```

### Configure Router Port Forwarding

1. Access your router admin panel (usually 192.168.1.1)
2. Find "Port Forwarding" or "Virtual Server" section
3. Add rules:
   - External Port 80 → Internal IP:80 (HTTP)
   - External Port 443 → Internal IP:443 (HTTPS)
   - External Port 22 → Internal IP:22 (SSH, optional)

### Update DNS Records

In your domain registrar (Namecheap, GoDaddy, etc.):

```
Type: A
Host: @
Value: YOUR_PUBLIC_IP
TTL: 3600

Type: A
Host: www
Value: YOUR_PUBLIC_IP
TTL: 3600
```

Wait 5-60 minutes for DNS propagation.

### Verify DNS

```bash
# Check DNS propagation
nslookup yourdomain.com
dig yourdomain.com

# Should show your public IP
```

---

## 🚀 Step 14: Start All Services

### Start Backend

```bash
# Using systemd
sudo systemctl start booklook
sudo systemctl status booklook

# Or manually
cd /opt/booklook
conda activate booklook
python main.py
```

### Start Frontend

```bash
cd /opt/booklook/frontend
pm2 start npm --name "booklook-frontend" -- start
pm2 save
```

### Verify Services

```bash
# Check backend
curl http://localhost:8000/

# Check frontend
curl http://localhost:3000/

# Check via domain
curl http://yourdomain.com/api/
```

---

## 📊 Step 15: Load Your Dataset

### Prepare CSV Files

Place your CSV files in a directory:
```bash
mkdir -p /opt/booklook/data/institutional_books
# Copy your CSV files here
```

### Run Import

```bash
cd /opt/booklook
conda activate booklook

# Import with progress logging
python load_institutional_dataset.py /opt/booklook/data/institutional_books \
  --batch-size 100 \
  --skip-existing 2>&1 | tee import_progress.log
```

### Monitor Import

```bash
# In another terminal
tail -f dataset_import.log

# Check database size
sudo -u postgres psql -d booklook -c "
SELECT 
    pg_size_pretty(pg_database_size('booklook')) as db_size,
    (SELECT COUNT(*) FROM books) as book_count,
    (SELECT COUNT(*) FROM book_pages) as page_count;
"
```

---

## 🎯 Step 16: Post-Deployment

### Optimize Database

```bash
sudo -u postgres psql -d booklook

-- Analyze tables
ANALYZE books;
ANALYZE book_pages;
ANALYZE authors;

-- Vacuum
VACUUM ANALYZE books;
VACUUM ANALYZE book_pages;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

### Test Application

```bash
# Test API
curl http://yourdomain.com/api/v1/books?page=1&page_size=10

# Test admin
# Visit: http://yourdomain.com/admin

# Test book reading
# Visit: http://yourdomain.com/books/1
```

---

## 🔍 Step 17: Troubleshooting

### Backend Not Starting

```bash
# Check logs
journalctl -u booklook -n 50

# Check if port is in use
sudo lsof -i :8000

# Test manually
cd /opt/booklook
conda activate booklook
python main.py
```

### Database Connection Issues

```bash
# Test connection
psql -U booklook_user -h localhost -d booklook

# Check PostgreSQL status
sudo systemctl status postgresql

# Check logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

### Domain Not Accessible

```bash
# Check Nginx
sudo nginx -t
sudo systemctl status nginx

# Check firewall
sudo ufw status

# Check DNS
nslookup yourdomain.com

# Check port forwarding
curl http://YOUR_PUBLIC_IP
```

### Import Errors

```bash
# Check error log
cat import_errors.json

# Check database space
df -h

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

---

## 📈 Step 18: Scaling Considerations

### For Large Datasets (300GB+)

1. **Increase PostgreSQL resources:**
   ```ini
   shared_buffers = 8GB
   effective_cache_size = 24GB
   work_mem = 50MB
   ```

2. **Use connection pooling:**
   ```bash
   pip install pgbouncer
   ```

3. **Consider read replicas:**
   - Setup PostgreSQL replication
   - Route read queries to replicas

4. **Optimize batch size:**
   ```bash
   # For large datasets, use smaller batches
   python load_institutional_dataset.py /path/to/data --batch-size 50
   ```

---

## 🎓 Maintenance

### Daily Tasks
- Monitor disk space
- Check application logs
- Verify backups

### Weekly Tasks
- Review error logs
- Optimize database (VACUUM)
- Update dependencies

### Monthly Tasks
- Security updates
- Performance review
- Backup testing

---

## 📞 Quick Reference

### Start Services
```bash
sudo systemctl start postgresql
sudo systemctl start redis
sudo systemctl start booklook
sudo systemctl start nginx
pm2 start booklook-frontend
```

### Stop Services
```bash
sudo systemctl stop booklook
pm2 stop booklook-frontend
```

### Restart Services
```bash
sudo systemctl restart booklook
pm2 restart booklook-frontend
sudo systemctl restart nginx
```

### View Logs
```bash
journalctl -u booklook -f
pm2 logs booklook-frontend
tail -f /var/log/nginx/access.log
```

### Database Commands
```bash
# Backup
pg_dump -U booklook_user booklook > backup.sql

# Restore
psql -U booklook_user booklook < backup.sql

# Connect
psql -U booklook_user -d booklook
```

---

## ✅ Deployment Checklist

- [ ] System packages installed
- [ ] PostgreSQL configured
- [ ] Redis configured
- [ ] Application cloned
- [ ] Python environment setup
- [ ] Environment variables configured
- [ ] Database migrations run
- [ ] Dataset imported
- [ ] Backend service running
- [ ] Frontend built and running
- [ ] Nginx configured
- [ ] SSL certificate installed
- [ ] Domain DNS configured
- [ ] Port forwarding setup
- [ ] Firewall configured
- [ ] Backups configured
- [ ] Monitoring setup
- [ ] Application tested

---

## 🎉 Success!

Your BookLook application should now be:
- ✅ Running on your local machine
- ✅ Accessible via your domain
- ✅ Secured with HTTPS
- ✅ Loaded with your dataset
- ✅ Production ready

**Access your application at: https://yourdomain.com**

---

*Last Updated: November 10, 2025*
*Version: 1.0*
*Status: Production Ready ✅*
