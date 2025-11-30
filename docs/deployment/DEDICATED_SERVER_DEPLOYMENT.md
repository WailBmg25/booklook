# BookLook Dedicated Server Deployment Guide

This guide provides step-by-step instructions for deploying BookLook on a dedicated server (bare metal or VPS) running Ubuntu/Debian Linux.

## Table of Contents

- [Hardware Requirements](#hardware-requirements)
- [Server Preparation](#server-preparation)
- [Software Installation](#software-installation)
- [Application Deployment](#application-deployment)
- [SSL/TLS Configuration](#ssltls-configuration)
- [Network Configuration](#network-configuration)
- [Performance Optimization](#performance-optimization)
- [Monitoring Setup](#monitoring-setup)
- [Maintenance Procedures](#maintenance-procedures)

## Hardware Requirements

### Minimum Requirements (Small Dataset < 50GB)

- **CPU**: 4 cores (2.0 GHz+)
- **RAM**: 8 GB
- **Storage**: 100 GB SSD
- **Network**: 100 Mbps
- **OS**: Ubuntu 20.04 LTS or Debian 11+

### Recommended Requirements (Medium Dataset 50-200GB)

- **CPU**: 8 cores (2.5 GHz+)
- **RAM**: 32 GB
- **Storage**: 500 GB NVMe SSD
- **Network**: 1 Gbps
- **OS**: Ubuntu 22.04 LTS

### Production Requirements (Large Dataset 200GB+)

- **CPU**: 16+ cores (3.0 GHz+)
- **RAM**: 64 GB+
- **Storage**: 1 TB+ NVMe SSD (RAID 10 recommended)
- **Network**: 10 Gbps
- **OS**: Ubuntu 22.04 LTS

### Storage Breakdown

For a 400GB book dataset:
- **Database**: ~400 GB (book content + metadata)
- **Indexes**: ~50 GB
- **Backups**: ~200 GB (compressed)
- **Logs**: ~10 GB
- **System**: ~20 GB
- **Buffer**: ~100 GB
- **Total**: ~780 GB minimum

## Server Preparation

### 1. Initial Server Setup

```bash
# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install essential tools
sudo apt-get install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    net-tools \
    ufw \
    fail2ban \
    unattended-upgrades

# Set timezone
sudo timedatectl set-timezone UTC

# Set hostname
sudo hostnamectl set-hostname booklook-prod
```

### 2. Create Application User

```bash
# Create dedicated user for the application
sudo adduser --disabled-password --gecos "" booklook

# Add to docker group (will be created later)
sudo usermod -aG sudo booklook

# Switch to application user
sudo su - booklook
```

### 3. Configure Firewall

```bash
# Enable UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (change port if using non-standard)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status verbose
```

### 4. Configure Fail2Ban

```bash
# Install fail2ban
sudo apt-get install -y fail2ban

# Create local configuration
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# Edit configuration
sudo nano /etc/fail2ban/jail.local
```

Add/modify these settings:

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = 22
logpath = /var/log/auth.log
```

```bash
# Restart fail2ban
sudo systemctl restart fail2ban
sudo systemctl enable fail2ban
```

## Software Installation

### 1. Install Docker

```bash
# Remove old versions
sudo apt-get remove docker docker-engine docker.io containerd runc

# Install dependencies
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
sudo usermod -aG docker booklook

# Enable Docker service
sudo systemctl enable docker
sudo systemctl start docker

# Verify installation
docker --version
docker compose version
```

### 2. Configure Docker

```bash
# Create Docker daemon configuration
sudo mkdir -p /etc/docker

sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "userland-proxy": false,
  "live-restore": true
}
EOF

# Restart Docker
sudo systemctl restart docker
```

### 3. Install Additional Tools

```bash
# Install PostgreSQL client (for management)
sudo apt-get install -y postgresql-client

# Install monitoring tools
sudo apt-get install -y \
    sysstat \
    iotop \
    nethogs

# Install backup tools
sudo apt-get install -y \
    rsync \
    pigz
```

## Application Deployment

### 1. Clone Repository

```bash
# Switch to application user
sudo su - booklook

# Create application directory
mkdir -p /home/booklook/apps
cd /home/booklook/apps

# Clone repository
git clone <your-repository-url> booklook
cd booklook

# Checkout production branch
git checkout main
```

### 2. Configure Environment

```bash
# Copy production environment template
cp .env.production.example .env.production

# Generate secrets
SECRET_KEY=$(openssl rand -hex 32)
NEXTAUTH_SECRET=$(openssl rand -base64 32)
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# Edit environment file
nano .env.production
```

Update these critical values:

```bash
# Application
APP_NAME="BookLook Production"
DEBUG=false
LOG_LEVEL=info

# Database (adjust based on your RAM)
POSTGRES_USER=booklook_user
POSTGRES_PASSWORD=<generated-password>
POSTGRES_DB=booklook_production
POSTGRES_SHARED_BUFFERS=16GB        # 25% of 64GB RAM
POSTGRES_EFFECTIVE_CACHE_SIZE=48GB  # 75% of 64GB RAM
POSTGRES_MAINTENANCE_WORK_MEM=4GB
POSTGRES_WORK_MEM=64MB
POSTGRES_MAX_CONNECTIONS=200

# Redis
REDIS_MAX_MEMORY=8gb

# Backend
BACKEND_PORT=8000
BACKEND_WORKERS=16                   # 2 * CPU cores
SECRET_KEY=<generated-secret>
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Frontend
FRONTEND_PORT=3000
NEXT_PUBLIC_API_URL=https://yourdomain.com/api
NEXTAUTH_URL=https://yourdomain.com
NEXTAUTH_SECRET=<generated-secret>

# Nginx
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443
```

```bash
# Secure the environment file
chmod 600 .env.production
```

### 3. Deploy Application

```bash
# Build and start services
./deploy.sh deploy

# This will:
# 1. Check requirements
# 2. Build Docker images
# 3. Start all services
# 4. Run database migrations
# 5. Perform health check

# Monitor deployment
./logs.sh all follow
```

### 4. Verify Deployment

```bash
# Check service status
./deploy.sh status

# Run health check
./health-check.sh full

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:3000
```

## SSL/TLS Configuration

### Option 1: Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt-get install -y certbot

# Stop Nginx temporarily
docker-compose -f docker-compose.prod.yml stop nginx

# Obtain certificate
sudo certbot certonly --standalone \
    -d yourdomain.com \
    -d www.yourdomain.com \
    --email admin@yourdomain.com \
    --agree-tos \
    --non-interactive

# Certificates will be in:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem

# Copy certificates to Docker volume
sudo mkdir -p docker/nginx/ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem \
    docker/nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem \
    docker/nginx/ssl/key.pem
sudo chmod 644 docker/nginx/ssl/cert.pem
sudo chmod 600 docker/nginx/ssl/key.pem

# Update Nginx configuration
nano docker/nginx/nginx.conf
```

Uncomment and update the HTTPS server block:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # ... rest of configuration
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

```bash
# Restart Nginx with SSL
docker-compose -f docker-compose.prod.yml --profile with-nginx up -d

# Set up auto-renewal
sudo crontab -e
```

Add this line:

```cron
0 0 * * 0 certbot renew --quiet && cp /etc/letsencrypt/live/yourdomain.com/*.pem /home/booklook/apps/booklook/docker/nginx/ssl/ && docker-compose -f /home/booklook/apps/booklook/docker-compose.prod.yml restart nginx
```

### Option 2: Custom SSL Certificate

```bash
# Copy your certificates
sudo mkdir -p docker/nginx/ssl
sudo cp /path/to/your/cert.pem docker/nginx/ssl/
sudo cp /path/to/your/key.pem docker/nginx/ssl/
sudo chmod 644 docker/nginx/ssl/cert.pem
sudo chmod 600 docker/nginx/ssl/key.pem

# Update Nginx configuration (same as above)
# Restart services
./deploy.sh restart
```

## Network Configuration

### 1. DNS Configuration

Point your domain to the server IP:

```
A Record:     yourdomain.com      → <server-ip>
A Record:     www.yourdomain.com  → <server-ip>
CNAME Record: api.yourdomain.com  → yourdomain.com
```

### 2. Reverse Proxy Setup

If using Nginx profile:

```bash
# Start with Nginx profile
docker-compose -f docker-compose.prod.yml --profile with-nginx up -d

# Verify Nginx is running
docker ps | grep nginx
curl http://localhost
```

### 3. Port Forwarding

If behind a router/firewall:
- Forward port 80 (HTTP) to server
- Forward port 443 (HTTPS) to server
- Keep port 22 (SSH) restricted to specific IPs

## Performance Optimization

### 1. System Tuning

```bash
# Edit sysctl configuration
sudo nano /etc/sysctl.conf
```

Add these optimizations:

```ini
# Network performance
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15

# File system
fs.file-max = 2097152
fs.inotify.max_user_watches = 524288

# Virtual memory
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
```

```bash
# Apply changes
sudo sysctl -p

# Set file limits
sudo nano /etc/security/limits.conf
```

Add:

```
* soft nofile 65535
* hard nofile 65535
* soft nproc 65535
* hard nproc 65535
```

### 2. PostgreSQL Tuning

The docker-compose configuration already includes optimizations, but you can further tune:

```bash
# Connect to PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres psql -U booklook_user -d booklook_production

# Check current settings
SHOW shared_buffers;
SHOW effective_cache_size;
SHOW work_mem;

# Analyze tables
ANALYZE;

# Vacuum database
VACUUM ANALYZE;
```

### 3. Disk I/O Optimization

```bash
# Check disk scheduler
cat /sys/block/sda/queue/scheduler

# Set to deadline for SSDs
echo deadline | sudo tee /sys/block/sda/queue/scheduler

# Make permanent
sudo nano /etc/rc.local
```

Add:

```bash
echo deadline > /sys/block/sda/queue/scheduler
```

## Monitoring Setup

### 1. System Monitoring

```bash
# Install monitoring tools
sudo apt-get install -y prometheus-node-exporter

# Enable and start
sudo systemctl enable prometheus-node-exporter
sudo systemctl start prometheus-node-exporter
```

### 2. Application Monitoring

```bash
# Create monitoring script
cat > /home/booklook/monitor.sh << 'EOF'
#!/bin/bash
cd /home/booklook/apps/booklook
./health-check.sh full > /var/log/booklook-health.log 2>&1
EOF

chmod +x /home/booklook/monitor.sh

# Add to crontab
crontab -e
```

Add:

```cron
*/5 * * * * /home/booklook/monitor.sh
```

### 3. Log Rotation

```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/booklook
```

Add:

```
/home/booklook/apps/booklook/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 booklook booklook
    sharedscripts
    postrotate
        docker-compose -f /home/booklook/apps/booklook/docker-compose.prod.yml restart backend
    endscript
}
```

## Maintenance Procedures

### Daily Tasks

```bash
# Health check
cd /home/booklook/apps/booklook
./health-check.sh full

# Check logs for errors
./logs.sh errors

# Monitor disk space
df -h

# Check service status
./deploy.sh status
```

### Weekly Tasks

```bash
# Create backup
./backup.sh full

# Check resource usage
docker stats --no-stream

# Review logs
./logs.sh all 1000 > weekly-logs.txt

# Update system packages
sudo apt-get update
sudo apt-get upgrade -y
```

### Monthly Tasks

```bash
# Cleanup old backups
./backup.sh cleanup 30

# Vacuum database
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production -c "VACUUM ANALYZE;"

# Update Docker images
docker-compose -f docker-compose.prod.yml pull
./deploy.sh restart

# Review and optimize
./health-check.sh full
```

### Backup Strategy

```bash
# Automated daily backups
crontab -e
```

Add:

```cron
# Daily backup at 2 AM
0 2 * * * cd /home/booklook/apps/booklook && ./backup.sh full

# Weekly cleanup (keep 30 days)
0 3 * * 0 cd /home/booklook/apps/booklook && ./backup.sh cleanup 30
```

### Disaster Recovery

```bash
# Restore from backup
cd /home/booklook/apps/booklook

# Stop services
./deploy.sh stop

# Restore database
./backup.sh restore backups/booklook_db_YYYYMMDD_HHMMSS.sql.gz

# Start services
./deploy.sh start

# Verify
./health-check.sh full
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
./logs.sh all

# Check disk space
df -h

# Check memory
free -h

# Restart services
./deploy.sh restart
```

### Database Connection Issues

```bash
# Check PostgreSQL logs
./logs.sh postgres 500

# Check connections
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "SELECT count(*) FROM pg_stat_activity;"

# Restart PostgreSQL
docker-compose -f docker-compose.prod.yml restart postgres
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Check slow queries
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Analyze and vacuum
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "VACUUM ANALYZE;"
```

## Security Checklist

- [ ] Firewall configured (UFW)
- [ ] Fail2Ban installed and configured
- [ ] SSH key authentication enabled
- [ ] Password authentication disabled
- [ ] SSL/TLS certificates installed
- [ ] Strong passwords generated
- [ ] Environment files secured (chmod 600)
- [ ] Regular security updates enabled
- [ ] Backup encryption configured
- [ ] Monitoring and alerting set up
- [ ] Log rotation configured
- [ ] Non-root user for application
- [ ] Database access restricted
- [ ] CORS properly configured

## Next Steps

After deployment:

1. Test all functionality thoroughly
2. Set up monitoring and alerting
3. Configure automated backups
4. Document any custom configurations
5. Create runbook for operations team
6. Plan for scaling if needed

## Support

For issues:
- Check logs: `./logs.sh errors`
- Run health check: `./health-check.sh`
- Review documentation in `docs/`
- Check system resources: `htop`, `df -h`, `free -h`

---

**Last Updated**: 2024
**Version**: 1.0
