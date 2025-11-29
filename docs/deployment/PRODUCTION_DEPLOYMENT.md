# Production Deployment Guide

## Using Gunicorn + Uvicorn for Production

BookLook uses **Gunicorn** with **Uvicorn workers** for production deployment, providing:
- Multiple worker processes for concurrent request handling
- Automatic worker restart on failure
- Graceful shutdowns and zero-downtime deployments
- Better resource utilization for large databases

## Quick Start

### Development Mode (Uvicorn only)
```bash
./start.sh
# or
./start.sh dev
```

### Production Mode (Gunicorn + Uvicorn)
```bash
./start.sh prod
```

## Manual Production Start

### Option 1: Using the production script
```bash
cd src
./start-production.sh
```

### Option 2: Direct Gunicorn command
```bash
cd src
gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --keep-alive 5
```

### Option 3: Using configuration file
```bash
cd src
gunicorn main:app --config gunicorn.conf.py
```

## Configuration

### Worker Count

The number of workers is automatically calculated as:
```
workers = (CPU cores × 2) + 1
```

You can override this:
```bash
WORKERS=8 ./start.sh prod
```

### Environment Variables

Create `src/.env` file:
```env
# Server Configuration
WORKERS=4
LOG_LEVEL=info

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/booklook
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
```

## Gunicorn Configuration

Edit `src/gunicorn.conf.py` to customize:

```python
# Worker processes
workers = 4  # Adjust based on CPU cores
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120  # For long-running queries
keepalive = 5

# Restart workers periodically (prevents memory leaks)
max_requests = 1000
max_requests_jitter = 50
```

## Performance Tuning

### For 400GB Database

1. **Worker Count**: Start with `(CPU cores × 2) + 1`
   ```bash
   # For 4 CPU cores
   WORKERS=9 gunicorn main:app --config gunicorn.conf.py
   ```

2. **Database Connection Pool**: Each worker needs connections
   ```python
   # In database.py or config
   pool_size = 10  # Per worker
   max_overflow = 20
   ```

3. **Timeout**: Increase for long queries
   ```python
   timeout = 120  # seconds
   ```

4. **Memory**: Monitor and adjust max_requests
   ```python
   max_requests = 1000  # Restart worker after 1000 requests
   ```

### Monitoring Workers

```bash
# Check running workers
ps aux | grep gunicorn

# Monitor logs
tail -f /var/log/gunicorn/access.log
tail -f /var/log/gunicorn/error.log
```

## Systemd Service (Linux)

Create `/etc/systemd/system/booklook.service`:

```ini
[Unit]
Description=BookLook FastAPI Application
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/booklook/src
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn main:app --config gunicorn.conf.py
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable booklook
sudo systemctl start booklook
sudo systemctl status booklook
```

## Docker Deployment

See `Dockerfile` for containerized deployment with Gunicorn.

```dockerfile
CMD ["gunicorn", "main:app", \
     "--config", "gunicorn.conf.py", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker"]
```

## Graceful Shutdown

Gunicorn handles graceful shutdowns automatically:

```bash
# Graceful reload (zero downtime)
kill -HUP <gunicorn-master-pid>

# Graceful shutdown
kill -TERM <gunicorn-master-pid>
```

## Load Balancing

For high traffic, use Nginx as a reverse proxy:

```nginx
upstream booklook_backend {
    server 127.0.0.1:8000;
    # Add more backend servers for horizontal scaling
    # server 127.0.0.1:8001;
    # server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name booklook.example.com;

    location / {
        proxy_pass http://booklook_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Troubleshooting

### Workers Dying
- Check memory usage: `free -h`
- Reduce worker count or increase RAM
- Check logs for errors

### Slow Responses
- Increase timeout: `--timeout 180`
- Check database query performance
- Monitor connection pool usage

### High CPU Usage
- Reduce worker count
- Check for infinite loops or heavy computations
- Profile with `py-spy`

## Benchmarking

Test your production setup:

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test with 1000 requests, 10 concurrent
ab -n 1000 -c 10 http://localhost:8000/

# Test with authentication
ab -n 1000 -c 10 -H "Authorization: Bearer <token>" http://localhost:8000/books
```

## Best Practices

1. ✅ Use Gunicorn + Uvicorn in production
2. ✅ Set worker count based on CPU cores
3. ✅ Configure database connection pooling
4. ✅ Enable access logging for monitoring
5. ✅ Use systemd or Docker for process management
6. ✅ Set up health checks
7. ✅ Monitor worker memory usage
8. ✅ Use Nginx for SSL and load balancing

## Next Steps

- Set up monitoring (Prometheus, Grafana)
- Configure log aggregation (ELK stack)
- Implement health check endpoints
- Set up automated backups
- Configure SSL certificates
