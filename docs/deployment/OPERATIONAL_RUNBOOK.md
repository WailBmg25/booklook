# BookLook Operational Runbook

This runbook provides standard operating procedures for managing and maintaining the BookLook production environment.

## Table of Contents

- [Daily Operations](#daily-operations)
- [Incident Response](#incident-response)
- [Common Procedures](#common-procedures)
- [Scaling Operations](#scaling-operations)
- [Security Procedures](#security-procedures)
- [Disaster Recovery](#disaster-recovery)
- [On-Call Guide](#on-call-guide)

## Daily Operations

### Morning Health Check (9:00 AM)

```bash
cd /home/booklook/apps/booklook

# 1. Run comprehensive health check
./health-check.sh full

# 2. Check service status
./deploy.sh status

# 3. Review overnight logs for errors
./logs.sh errors | tail -100

# 4. Check disk space
df -h

# 5. Check database size
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "SELECT pg_size_pretty(pg_database_size('booklook_production'));"

# 6. Check active users (last 24 hours)
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "SELECT COUNT(DISTINCT user_id) FROM reading_progress 
        WHERE last_read_at > NOW() - INTERVAL '24 hours';"

# 7. Check for failed backups
ls -lh backups/ | tail -5
```

### Evening Review (6:00 PM)

```bash
# 1. Review daily statistics
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production << EOF
SELECT 
    'Books' as metric, COUNT(*) as count FROM books
UNION ALL
SELECT 'Users', COUNT(*) FROM users
UNION ALL
SELECT 'Reviews Today', COUNT(*) FROM reviews 
    WHERE created_at > CURRENT_DATE
UNION ALL
SELECT 'Active Users Today', COUNT(DISTINCT user_id) FROM reading_progress 
    WHERE last_read_at > CURRENT_DATE;
EOF

# 2. Check resource usage
docker stats --no-stream

# 3. Verify backup completed
ls -lh backups/booklook_db_$(date +%Y%m%d)*.sql.gz

# 4. Review slow queries
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "SELECT query, calls, mean_time FROM pg_stat_statements 
        WHERE mean_time > 1000 ORDER BY mean_time DESC LIMIT 5;"
```

## Incident Response

### Service Down

**Symptoms:**
- Health check fails
- Users cannot access application
- 502/503 errors

**Response Procedure:**

```bash
# 1. Check service status
./deploy.sh status

# 2. Check logs for errors
./logs.sh all 200

# 3. Identify failed service
docker ps -a

# 4. Restart failed service
docker-compose -f docker-compose.prod.yml restart <service-name>

# 5. If restart fails, check logs
./logs.sh <service-name> 500

# 6. Verify recovery
./health-check.sh full

# 7. Document incident
echo "$(date): Service down - <service-name> - Resolved by restart" >> incidents.log
```

### Database Connection Issues

**Symptoms:**
- "Connection refused" errors
- "Too many connections" errors
- Slow query performance

**Response Procedure:**

```bash
# 1. Check PostgreSQL status
docker-compose -f docker-compose.prod.yml ps postgres

# 2. Check active connections
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# 3. Check for long-running queries
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "SELECT pid, now() - query_start AS duration, query 
        FROM pg_stat_activity 
        WHERE state = 'active' AND now() - query_start > interval '5 minutes';"

# 4. Kill long-running queries if needed
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "SELECT pg_terminate_backend(<pid>);"

# 5. Restart PostgreSQL if necessary
docker-compose -f docker-compose.prod.yml restart postgres

# 6. Verify recovery
./health-check.sh database
```

### High CPU Usage

**Symptoms:**
- Slow response times
- High load average
- CPU at 100%

**Response Procedure:**

```bash
# 1. Identify resource-intensive process
htop
docker stats

# 2. Check for slow queries
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "SELECT pid, query, state, now() - query_start AS duration 
        FROM pg_stat_activity 
        WHERE state != 'idle' ORDER BY duration DESC LIMIT 10;"

# 3. Check backend logs for errors
./logs.sh backend 500

# 4. If specific query is causing issue, kill it
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "SELECT pg_terminate_backend(<pid>);"

# 5. Consider scaling if sustained high usage
# See Scaling Operations section
```

### Disk Space Full

**Symptoms:**
- "No space left on device" errors
- Database write failures
- Application crashes

**Response Procedure:**

```bash
# 1. Check disk usage
df -h

# 2. Identify large files/directories
du -sh /* | sort -h
du -sh /home/booklook/apps/booklook/* | sort -h

# 3. Clean up Docker
docker system prune -a -f

# 4. Remove old backups
cd /home/booklook/apps/booklook
./backup.sh cleanup 7  # Keep only 7 days

# 5. Clean up logs
find logs/ -name "*.log" -mtime +7 -delete

# 6. If still critical, remove old data
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "DELETE FROM reviews WHERE created_at < NOW() - INTERVAL '2 years';"

# 7. Vacuum database
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "VACUUM FULL;"

# 8. Verify space recovered
df -h
```

### Memory Issues

**Symptoms:**
- OOM (Out of Memory) errors
- Services being killed
- Swap usage high

**Response Procedure:**

```bash
# 1. Check memory usage
free -h
docker stats

# 2. Identify memory-intensive containers
docker stats --no-stream | sort -k 4 -h

# 3. Reduce PostgreSQL memory if needed
# Edit .env.production
POSTGRES_SHARED_BUFFERS=8GB  # Reduce from 16GB
POSTGRES_WORK_MEM=32MB       # Reduce from 64MB

# 4. Restart services
./deploy.sh restart

# 5. Monitor memory usage
watch -n 5 'free -h'

# 6. Consider adding swap or upgrading server
```

## Common Procedures

### Deploying Updates

```bash
# 1. Announce maintenance window
# Send notification to users

# 2. Create backup
./backup.sh full

# 3. Pull latest code
cd /home/booklook/apps/booklook
git pull origin main

# 4. Check for database migrations
ls src/alembic/versions/

# 5. Stop services
./deploy.sh stop

# 6. Build new images
./deploy.sh build

# 7. Start services
./deploy.sh start

# 8. Run migrations
./deploy.sh migrate

# 9. Verify deployment
./health-check.sh full

# 10. Monitor logs
./logs.sh all 100 follow

# 11. Rollback if issues
git checkout <previous-commit>
./deploy.sh deploy
```

### Adding New Admin User

```bash
# 1. Connect to database
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production

# 2. Create user with admin privileges
INSERT INTO users (email, first_name, last_name, password_hash, is_admin, is_active)
VALUES (
    'admin@example.com',
    'Admin',
    'User',
    '<bcrypt-hashed-password>',
    true,
    true
);

# 3. Verify
SELECT id, email, is_admin FROM users WHERE email = 'admin@example.com';
```

### Resetting User Password

```bash
# 1. Generate new password hash
python3 << EOF
import bcrypt
password = "new_password_here"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print(hashed.decode('utf-8'))
EOF

# 2. Update user password
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "UPDATE users SET password_hash = '<hashed-password>' 
        WHERE email = 'user@example.com';"
```

### Clearing Cache

```bash
# 1. Clear Redis cache
docker-compose -f docker-compose.prod.yml exec redis redis-cli FLUSHALL

# 2. Verify
docker-compose -f docker-compose.prod.yml exec redis redis-cli INFO stats

# 3. Monitor cache rebuild
./logs.sh backend 100 follow
```

### Database Maintenance

```bash
# Weekly maintenance (Sunday 2 AM)
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production << EOF
-- Analyze tables
ANALYZE VERBOSE;

-- Check for bloat
SELECT 
    schemaname,
    tablename,
    n_dead_tup,
    n_live_tup,
    ROUND(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_pct
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_dead_tup DESC
LIMIT 10;

-- Vacuum if needed
VACUUM ANALYZE;
EOF
```

## Scaling Operations

### Vertical Scaling (Increase Resources)

```bash
# 1. Create backup
./backup.sh full

# 2. Stop services
./deploy.sh stop

# 3. Update server resources (cloud provider or hardware)
# - Increase CPU cores
# - Increase RAM
# - Increase disk space

# 4. Update configuration
nano .env.production
# Adjust POSTGRES_SHARED_BUFFERS, BACKEND_WORKERS, etc.

# 5. Start services
./deploy.sh start

# 6. Verify
./health-check.sh full
docker stats
```

### Horizontal Scaling (Add Instances)

```bash
# 1. Set up load balancer (Nginx or cloud LB)

# 2. Deploy additional backend instances
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# 3. Configure load balancer to distribute traffic

# 4. Verify all instances healthy
./health-check.sh full

# 5. Monitor load distribution
./logs.sh nginx 100 follow
```

### Database Read Replicas

```bash
# 1. Create read replica (cloud provider or manual setup)

# 2. Configure application to use replica for reads
# Update .env.production:
DATABASE_READ_URL=postgresql://user:pass@replica:5432/db

# 3. Restart backend
docker-compose -f docker-compose.prod.yml restart backend

# 4. Monitor replication lag
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "SELECT * FROM pg_stat_replication;"
```

## Security Procedures

### Security Audit

```bash
# Monthly security audit checklist

# 1. Check for unauthorized users
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "SELECT id, email, is_admin, created_at FROM users 
        WHERE is_admin = true ORDER BY created_at DESC;"

# 2. Review failed login attempts
./logs.sh backend 1000 | grep "authentication failed"

# 3. Check for suspicious activity
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "SELECT user_id, COUNT(*) as review_count 
        FROM reviews 
        WHERE created_at > NOW() - INTERVAL '1 day' 
        GROUP BY user_id 
        HAVING COUNT(*) > 50;"

# 4. Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# 5. Update Docker images
docker-compose -f docker-compose.prod.yml pull
./deploy.sh restart

# 6. Review firewall rules
sudo ufw status verbose

# 7. Check SSL certificate expiry
openssl x509 -in docker/nginx/ssl/cert.pem -noout -dates
```

### Responding to Security Incident

```bash
# 1. Immediately isolate affected systems
./deploy.sh stop

# 2. Create forensic backup
./backup.sh full
cp -r logs/ /secure/location/incident-$(date +%Y%m%d)/

# 3. Analyze logs
./logs.sh all 10000 > incident-logs.txt

# 4. Identify compromised accounts
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "SELECT * FROM users WHERE last_login > '<incident-time>';"

# 5. Reset passwords for affected accounts
# See "Resetting User Password" procedure

# 6. Update secrets
# Generate new SECRET_KEY and NEXTAUTH_SECRET
# Update .env.production
# Restart services

# 7. Document incident
echo "$(date): Security incident - <details>" >> security-incidents.log

# 8. Notify stakeholders
```

## Disaster Recovery

### Complete System Failure

```bash
# 1. Provision new server (see deployment guides)

# 2. Install Docker and dependencies

# 3. Clone repository
git clone <repository-url> /home/booklook/apps/booklook
cd /home/booklook/apps/booklook

# 4. Restore environment configuration
# Copy .env.production from backup

# 5. Deploy application
./deploy.sh build
./deploy.sh start

# 6. Restore database from backup
./backup.sh restore /path/to/backup/booklook_db_YYYYMMDD_HHMMSS.sql.gz

# 7. Verify restoration
./health-check.sh full

# 8. Update DNS if IP changed

# 9. Monitor for issues
./logs.sh all 500 follow
```

### Database Corruption

```bash
# 1. Stop application
./deploy.sh stop

# 2. Attempt database repair
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "REINDEX DATABASE booklook_production;"

# 3. If repair fails, restore from backup
./backup.sh restore backups/booklook_db_YYYYMMDD_HHMMSS.sql.gz

# 4. Verify data integrity
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production << EOF
SELECT COUNT(*) FROM books;
SELECT COUNT(*) FROM book_pages;
SELECT COUNT(*) FROM users;
EOF

# 5. Start application
./deploy.sh start

# 6. Verify functionality
./health-check.sh full
```

### Data Loss Recovery

```bash
# 1. Identify extent of data loss
# Check database, compare with backups

# 2. Restore from most recent backup
./backup.sh restore backups/booklook_db_YYYYMMDD_HHMMSS.sql.gz

# 3. If using WAL archiving, replay WAL files
# See DATABASE_OPTIMIZATION.md for PITR procedure

# 4. Verify restored data
# Run data integrity checks

# 5. Communicate with users about data loss
# Be transparent about what was lost

# 6. Implement additional backup measures
# Increase backup frequency
# Add off-site backups
```

## On-Call Guide

### On-Call Responsibilities

- Monitor alerts and notifications
- Respond to incidents within 15 minutes
- Escalate critical issues
- Document all incidents
- Perform daily health checks

### Alert Severity Levels

**P1 - Critical (Immediate Response)**
- Complete service outage
- Data loss
- Security breach
- Database corruption

**P2 - High (Response within 1 hour)**
- Partial service degradation
- High error rates
- Performance issues affecting users
- Disk space critical

**P3 - Medium (Response within 4 hours)**
- Non-critical errors
- Slow queries
- Cache issues
- Minor performance degradation

**P4 - Low (Response within 24 hours)**
- Warnings in logs
- Monitoring gaps
- Documentation updates needed

### Escalation Contacts

```
Primary On-Call: <phone> <email>
Secondary On-Call: <phone> <email>
Database Admin: <phone> <email>
Security Team: <phone> <email>
Management: <phone> <email>
```

### Quick Reference Commands

```bash
# Health check
./health-check.sh full

# View logs
./logs.sh all 200
./logs.sh errors

# Service status
./deploy.sh status

# Restart service
docker-compose -f docker-compose.prod.yml restart <service>

# Database connections
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# Disk space
df -h

# Memory usage
free -h

# Docker stats
docker stats --no-stream

# Create backup
./backup.sh full
```

### Post-Incident Checklist

- [ ] Incident resolved and verified
- [ ] Root cause identified
- [ ] Incident documented
- [ ] Stakeholders notified
- [ ] Preventive measures identified
- [ ] Runbook updated if needed
- [ ] Post-mortem scheduled (for P1/P2)

## Maintenance Windows

### Scheduled Maintenance

**Weekly (Sunday 2:00 AM - 4:00 AM UTC)**
- Database maintenance (VACUUM, ANALYZE)
- Log rotation
- Backup verification

**Monthly (First Sunday 3:00 AM - 6:00 AM UTC)**
- System updates
- Docker image updates
- Security patches
- Database reindexing

**Quarterly**
- Full system audit
- Disaster recovery test
- Performance review
- Capacity planning

### Emergency Maintenance

```bash
# 1. Notify users (if possible)
# Post maintenance notice

# 2. Create backup
./backup.sh full

# 3. Perform maintenance
# Follow specific procedure

# 4. Verify system health
./health-check.sh full

# 5. Monitor for issues
./logs.sh all 200 follow

# 6. Update status page
# Notify users of completion
```

## Contact Information

### Support Channels

- **Email**: support@booklook.com
- **Slack**: #booklook-ops
- **PagerDuty**: <pagerduty-url>
- **Status Page**: status.booklook.com

### External Services

- **Cloud Provider**: <provider-support>
- **DNS Provider**: <dns-support>
- **SSL Certificate**: <ssl-support>
- **Monitoring**: <monitoring-support>

## Additional Resources

- [Deployment Guides](./DEDICATED_SERVER_DEPLOYMENT.md)
- [Database Optimization](./DATABASE_OPTIMIZATION.md)
- [Data Loading Guide](./DATA_LOADING_GUIDE.md)
- [Docker Deployment](../DOCKER_DEPLOYMENT.md)

---

**Last Updated**: 2024
**Version**: 1.0
**Review Schedule**: Quarterly
