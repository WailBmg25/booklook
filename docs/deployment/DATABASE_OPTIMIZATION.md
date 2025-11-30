# BookLook Database Optimization and Maintenance Guide

This guide covers PostgreSQL optimization, maintenance procedures, and performance tuning for BookLook's large-scale database operations (400GB+).

## Table of Contents

- [Configuration Optimization](#configuration-optimization)
- [Indexing Strategy](#indexing-strategy)
- [Query Optimization](#query-optimization)
- [Maintenance Procedures](#maintenance-procedures)
- [Performance Monitoring](#performance-monitoring)
- [Backup and Recovery](#backup-and-recovery)
- [Troubleshooting](#troubleshooting)

## Configuration Optimization

### PostgreSQL Configuration for Large Datasets

#### Memory Settings

Based on available RAM, configure these settings in `.env.production`:

**For 64GB RAM Server:**
```bash
POSTGRES_SHARED_BUFFERS=16GB          # 25% of RAM
POSTGRES_EFFECTIVE_CACHE_SIZE=48GB    # 75% of RAM
POSTGRES_MAINTENANCE_WORK_MEM=4GB     # For VACUUM, CREATE INDEX
POSTGRES_WORK_MEM=64MB                # Per query operation
POSTGRES_MAX_CONNECTIONS=200
```

**For 32GB RAM Server:**
```bash
POSTGRES_SHARED_BUFFERS=8GB
POSTGRES_EFFECTIVE_CACHE_SIZE=24GB
POSTGRES_MAINTENANCE_WORK_MEM=2GB
POSTGRES_WORK_MEM=32MB
POSTGRES_MAX_CONNECTIONS=150
```

**For 16GB RAM Server:**
```bash
POSTGRES_SHARED_BUFFERS=4GB
POSTGRES_EFFECTIVE_CACHE_SIZE=12GB
POSTGRES_MAINTENANCE_WORK_MEM=1GB
POSTGRES_WORK_MEM=16MB
POSTGRES_MAX_CONNECTIONS=100
```

#### Additional PostgreSQL Settings

Connect to PostgreSQL and apply these settings:

```sql
-- Connect to database
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production

-- Checkpoint settings
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Planner settings
ALTER SYSTEM SET random_page_cost = 1.1;  -- For SSD
ALTER SYSTEM SET effective_io_concurrency = 200;  -- For SSD

-- Parallel query settings
ALTER SYSTEM SET max_worker_processes = 8;
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;
ALTER SYSTEM SET max_parallel_workers = 8;
ALTER SYSTEM SET max_parallel_maintenance_workers = 4;

-- Autovacuum settings
ALTER SYSTEM SET autovacuum_max_workers = 4;
ALTER SYSTEM SET autovacuum_naptime = '10s';
ALTER SYSTEM SET autovacuum_vacuum_scale_factor = 0.05;
ALTER SYSTEM SET autovacuum_analyze_scale_factor = 0.02;

-- Reload configuration
SELECT pg_reload_conf();

-- Verify settings
SHOW shared_buffers;
SHOW effective_cache_size;
SHOW work_mem;
```

### Connection Pooling

For high-traffic scenarios, configure connection pooling:

```bash
# Install PgBouncer
docker-compose -f docker-compose.prod.yml exec postgres \
    apt-get update && apt-get install -y pgbouncer

# Configure PgBouncer
cat > /etc/pgbouncer/pgbouncer.ini << EOF
[databases]
booklook_production = host=localhost port=5432 dbname=booklook_production

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
reserve_pool_size = 5
reserve_pool_timeout = 3
EOF
```

## Indexing Strategy

### Core Indexes

These indexes are essential for BookLook's performance:

```sql
-- Books table indexes
CREATE INDEX IF NOT EXISTS idx_books_title_gin 
    ON books USING gin(to_tsvector('english', title));

CREATE INDEX IF NOT EXISTS idx_books_isbn 
    ON books(isbn) WHERE isbn IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_books_publication_year 
    ON books(publication_year) WHERE publication_year IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_books_average_rating 
    ON books(average_rating DESC) WHERE average_rating > 0;

CREATE INDEX IF NOT EXISTS idx_books_created_at 
    ON books(created_at DESC);

-- Book pages indexes
CREATE INDEX IF NOT EXISTS idx_book_pages_book_id 
    ON book_pages(book_id);

CREATE INDEX IF NOT EXISTS idx_book_pages_book_page 
    ON book_pages(book_id, page_number);

CREATE INDEX IF NOT EXISTS idx_book_pages_content_gin 
    ON book_pages USING gin(to_tsvector('english', content));

-- Authors indexes
CREATE INDEX IF NOT EXISTS idx_authors_name 
    ON authors(name);

CREATE INDEX IF NOT EXISTS idx_authors_name_gin 
    ON authors USING gin(to_tsvector('english', name));

-- Book-Author relationship
CREATE INDEX IF NOT EXISTS idx_book_authors_book_id 
    ON book_authors(book_id);

CREATE INDEX IF NOT EXISTS idx_book_authors_author_id 
    ON book_authors(author_id);

-- Reviews indexes
CREATE INDEX IF NOT EXISTS idx_reviews_book_id 
    ON reviews(book_id);

CREATE INDEX IF NOT EXISTS idx_reviews_user_id 
    ON reviews(user_id);

CREATE INDEX IF NOT EXISTS idx_reviews_rating 
    ON reviews(rating);

CREATE INDEX IF NOT EXISTS idx_reviews_created_at 
    ON reviews(created_at DESC);

-- Reading progress indexes
CREATE INDEX IF NOT EXISTS idx_reading_progress_user_book 
    ON reading_progress(user_id, book_id);

CREATE INDEX IF NOT EXISTS idx_reading_progress_last_read 
    ON reading_progress(last_read_at DESC);

-- Users indexes
CREATE INDEX IF NOT EXISTS idx_users_email 
    ON users(email);

CREATE INDEX IF NOT EXISTS idx_users_created_at 
    ON users(created_at DESC);
```

### Analyze Index Usage

```sql
-- Check index usage statistics
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan ASC;

-- Find unused indexes (idx_scan = 0)
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public' 
    AND idx_scan = 0
    AND indexrelname NOT LIKE '%_pkey';

-- Drop unused indexes (carefully!)
-- DROP INDEX IF EXISTS index_name;
```

### Partial Indexes

For better performance on filtered queries:

```sql
-- Index only active users
CREATE INDEX idx_users_active 
    ON users(id) WHERE is_active = true;

-- Index only books with ratings
CREATE INDEX idx_books_rated 
    ON books(average_rating DESC) WHERE average_rating > 0;

-- Index recent reviews
CREATE INDEX idx_reviews_recent 
    ON reviews(created_at DESC) 
    WHERE created_at > CURRENT_DATE - INTERVAL '1 year';
```

## Query Optimization

### Analyze Slow Queries

```sql
-- Enable query logging
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1 second
ALTER SYSTEM SET log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h ';
SELECT pg_reload_conf();

-- Install pg_stat_statements extension
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- View slowest queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time,
    stddev_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 20;

-- Reset statistics
SELECT pg_stat_statements_reset();
```

### Common Query Patterns

#### Full-Text Search Optimization

```sql
-- Create GIN index for full-text search
CREATE INDEX idx_books_title_content_gin 
    ON books USING gin(
        to_tsvector('english', title || ' ' || COALESCE(description, ''))
    );

-- Optimized search query
EXPLAIN ANALYZE
SELECT id, title, average_rating
FROM books
WHERE to_tsvector('english', title || ' ' || COALESCE(description, '')) 
    @@ to_tsquery('english', 'search & term');
```

#### Pagination Optimization

```sql
-- Use keyset pagination instead of OFFSET
-- Bad (slow for large offsets):
SELECT * FROM books ORDER BY id LIMIT 20 OFFSET 10000;

-- Good (fast):
SELECT * FROM books WHERE id > 10000 ORDER BY id LIMIT 20;

-- For complex sorting:
CREATE INDEX idx_books_rating_id ON books(average_rating DESC, id);

SELECT * FROM books 
WHERE (average_rating, id) < (4.5, 10000)
ORDER BY average_rating DESC, id DESC
LIMIT 20;
```

#### Join Optimization

```sql
-- Analyze join performance
EXPLAIN (ANALYZE, BUFFERS)
SELECT b.*, a.name as author_name
FROM books b
JOIN book_authors ba ON b.id = ba.book_id
JOIN authors a ON ba.author_id = a.id
WHERE b.publication_year > 2000
LIMIT 100;

-- Create covering index if needed
CREATE INDEX idx_book_authors_covering 
    ON book_authors(book_id, author_id);
```

### Query Plan Analysis

```sql
-- Analyze query plan
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT * FROM books WHERE title ILIKE '%search%';

-- Key metrics to look for:
-- - Seq Scan (bad for large tables)
-- - Index Scan (good)
-- - Bitmap Heap Scan (good for multiple conditions)
-- - Nested Loop (can be slow)
-- - Hash Join (usually fast)
```

## Maintenance Procedures

### Daily Maintenance

```bash
#!/bin/bash
# daily_maintenance.sh

# Check database size
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "SELECT pg_size_pretty(pg_database_size('booklook_production'));"

# Check table bloat
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "SELECT schemaname, tablename, 
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
        FROM pg_tables WHERE schemaname = 'public' 
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 10;"

# Check for long-running queries
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
        FROM pg_stat_activity 
        WHERE state = 'active' AND now() - pg_stat_activity.query_start > interval '5 minutes';"
```

### Weekly Maintenance

```sql
-- Run ANALYZE on all tables
ANALYZE VERBOSE;

-- Check for dead tuples
SELECT 
    schemaname,
    tablename,
    n_live_tup,
    n_dead_tup,
    n_dead_tup * 100 / NULLIF(n_live_tup + n_dead_tup, 0) AS dead_pct,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_dead_tup DESC;

-- Manual VACUUM if needed (autovacuum should handle this)
VACUUM ANALYZE books;
VACUUM ANALYZE book_pages;
VACUUM ANALYZE reviews;
```

### Monthly Maintenance

```sql
-- Full VACUUM (requires downtime or low traffic)
VACUUM FULL ANALYZE books;
VACUUM FULL ANALYZE book_pages;

-- Reindex tables
REINDEX TABLE books;
REINDEX TABLE book_pages;
REINDEX TABLE authors;

-- Update statistics
ANALYZE VERBOSE;

-- Check for index bloat
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Automated Maintenance Script

```bash
#!/bin/bash
# automated_maintenance.sh

# Weekly maintenance (run on Sunday at 2 AM)
if [ $(date +%u) -eq 7 ]; then
    docker-compose -f docker-compose.prod.yml exec -T postgres \
        psql -U booklook_user -d booklook_production \
        -c "VACUUM ANALYZE;"
fi

# Monthly maintenance (run on 1st of month at 3 AM)
if [ $(date +%d) -eq 01 ]; then
    docker-compose -f docker-compose.prod.yml exec -T postgres \
        psql -U booklook_user -d booklook_production \
        -c "REINDEX DATABASE booklook_production;"
fi

# Add to crontab:
# 0 2 * * 0 /home/booklook/apps/booklook/automated_maintenance.sh
# 0 3 1 * * /home/booklook/apps/booklook/automated_maintenance.sh
```

## Performance Monitoring

### Key Metrics to Monitor

```sql
-- Database connections
SELECT count(*) as connections, state
FROM pg_stat_activity
GROUP BY state;

-- Cache hit ratio (should be > 99%)
SELECT 
    sum(heap_blks_read) as heap_read,
    sum(heap_blks_hit) as heap_hit,
    sum(heap_blks_hit) * 100 / 
        NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0) as cache_hit_ratio
FROM pg_statio_user_tables;

-- Index hit ratio (should be > 99%)
SELECT 
    sum(idx_blks_read) as idx_read,
    sum(idx_blks_hit) as idx_hit,
    sum(idx_blks_hit) * 100 / 
        NULLIF(sum(idx_blks_hit) + sum(idx_blks_read), 0) as idx_hit_ratio
FROM pg_statio_user_indexes;

-- Transaction rate
SELECT 
    xact_commit + xact_rollback as total_transactions,
    xact_commit,
    xact_rollback,
    xact_rollback * 100 / NULLIF(xact_commit + xact_rollback, 0) as rollback_pct
FROM pg_stat_database
WHERE datname = 'booklook_production';

-- Table I/O statistics
SELECT 
    schemaname,
    tablename,
    heap_blks_read,
    heap_blks_hit,
    idx_blks_read,
    idx_blks_hit
FROM pg_statio_user_tables
WHERE schemaname = 'public'
ORDER BY heap_blks_read + idx_blks_read DESC
LIMIT 10;
```

### Monitoring Script

```bash
#!/bin/bash
# monitor_database.sh

echo "=== Database Performance Report ==="
echo "Generated: $(date)"
echo ""

# Database size
echo "Database Size:"
docker-compose -f docker-compose.prod.yml exec -T postgres \
    psql -U booklook_user -d booklook_production -t \
    -c "SELECT pg_size_pretty(pg_database_size('booklook_production'));"
echo ""

# Active connections
echo "Active Connections:"
docker-compose -f docker-compose.prod.yml exec -T postgres \
    psql -U booklook_user -d booklook_production -t \
    -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"
echo ""

# Cache hit ratio
echo "Cache Hit Ratio:"
docker-compose -f docker-compose.prod.yml exec -T postgres \
    psql -U booklook_user -d booklook_production -t \
    -c "SELECT ROUND(sum(heap_blks_hit) * 100.0 / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0), 2) || '%' 
        FROM pg_statio_user_tables;"
echo ""

# Slow queries
echo "Slow Queries (> 1 second):"
docker-compose -f docker-compose.prod.yml exec -T postgres \
    psql -U booklook_user -d booklook_production \
    -c "SELECT query, calls, mean_time FROM pg_stat_statements 
        WHERE mean_time > 1000 ORDER BY mean_time DESC LIMIT 5;"
echo ""

# Run every hour:
# 0 * * * * /home/booklook/apps/booklook/monitor_database.sh >> /var/log/db_monitor.log
```

## Backup and Recovery

### Backup Strategy

```bash
# Full backup (daily at 2 AM)
0 2 * * * cd /home/booklook/apps/booklook && ./backup.sh full

# Incremental backup using WAL archiving
# Edit postgresql.conf:
wal_level = replica
archive_mode = on
archive_command = 'cp %p /mnt/backup/wal_archive/%f'
```

### Point-in-Time Recovery (PITR)

```bash
# Enable WAL archiving
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "ALTER SYSTEM SET wal_level = 'replica';"
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "ALTER SYSTEM SET archive_mode = 'on';"

# Restart PostgreSQL
docker-compose -f docker-compose.prod.yml restart postgres

# Create base backup
docker-compose -f docker-compose.prod.yml exec postgres \
    pg_basebackup -U booklook_user -D /mnt/backup/base -Ft -z -P

# Restore to specific point in time
# 1. Stop PostgreSQL
# 2. Restore base backup
# 3. Create recovery.conf with target time
# 4. Start PostgreSQL
```

### Backup Verification

```bash
# Test restore on separate instance
docker run --name postgres-test -e POSTGRES_PASSWORD=test -d postgres:15
docker cp backup.sql.gz postgres-test:/tmp/
docker exec postgres-test gunzip /tmp/backup.sql.gz
docker exec postgres-test psql -U postgres -f /tmp/backup.sql

# Verify data
docker exec postgres-test psql -U postgres -c "SELECT COUNT(*) FROM books;"
```

## Troubleshooting

### High CPU Usage

```sql
-- Find CPU-intensive queries
SELECT 
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query,
    state
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY duration DESC;

-- Kill problematic query
SELECT pg_terminate_backend(pid);
```

### High Memory Usage

```bash
# Check PostgreSQL memory
docker stats booklook-postgres-1

# Check shared buffers usage
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "SHOW shared_buffers;"

# Reduce work_mem if needed
ALTER SYSTEM SET work_mem = '32MB';
SELECT pg_reload_conf();
```

### Slow Queries

```sql
-- Enable query logging
ALTER SYSTEM SET log_min_duration_statement = 500;
SELECT pg_reload_conf();

-- Analyze slow query
EXPLAIN (ANALYZE, BUFFERS) <your_slow_query>;

-- Check missing indexes
SELECT 
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    seq_tup_read / NULLIF(seq_scan, 0) as avg_seq_tup
FROM pg_stat_user_tables
WHERE schemaname = 'public'
    AND seq_scan > 0
ORDER BY seq_tup_read DESC
LIMIT 10;
```

### Lock Contention

```sql
-- Check for locks
SELECT 
    pid,
    usename,
    pg_blocking_pids(pid) as blocked_by,
    query as blocked_query
FROM pg_stat_activity
WHERE cardinality(pg_blocking_pids(pid)) > 0;

-- Kill blocking query
SELECT pg_terminate_backend(<blocking_pid>);
```

### Database Bloat

```sql
-- Check table bloat
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    n_dead_tup,
    n_live_tup,
    ROUND(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_pct
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_dead_tup DESC;

-- Fix with VACUUM FULL (requires downtime)
VACUUM FULL ANALYZE books;
```

## Performance Checklist

- [ ] Shared buffers set to 25% of RAM
- [ ] Effective cache size set to 75% of RAM
- [ ] All critical indexes created
- [ ] Autovacuum enabled and tuned
- [ ] Query logging enabled for slow queries
- [ ] pg_stat_statements extension installed
- [ ] Regular ANALYZE scheduled
- [ ] Backup strategy implemented
- [ ] Monitoring in place
- [ ] Cache hit ratio > 99%
- [ ] Index hit ratio > 99%
- [ ] No long-running queries
- [ ] No table bloat
- [ ] Connection pooling configured

## Additional Resources

- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [PgTune](https://pgtune.leopard.in.ua/) - Configuration calculator
- [explain.depesz.com](https://explain.depesz.com/) - Query plan visualizer
- [PostgreSQL Monitoring](https://www.postgresql.org/docs/current/monitoring.html)

---

**Last Updated**: 2024
**Version**: 1.0
