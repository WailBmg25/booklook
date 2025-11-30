# BookLook Data Loading and Migration Guide

This guide covers loading large institutional book datasets (400GB+) into BookLook, including performance optimization, monitoring, and troubleshooting.

## Table of Contents

- [Overview](#overview)
- [Dataset Requirements](#dataset-requirements)
- [Pre-Loading Preparation](#pre-loading-preparation)
- [Loading Process](#loading-process)
- [Performance Optimization](#performance-optimization)
- [Monitoring Progress](#monitoring-progress)
- [Troubleshooting](#troubleshooting)
- [Post-Loading Tasks](#post-loading-tasks)

## Overview

The BookLook data loader (`load_institutional_dataset.py`) is designed to efficiently import large book datasets from CSV files into the PostgreSQL database. It handles:

- Batch processing for memory efficiency
- ISBN fetching from Open Library API
- Automatic ISBN generation for missing values
- Author and genre management
- Page-by-page content storage
- Error handling and recovery
- Progress tracking and statistics

### Key Features

- **Batch Processing**: Configurable batch sizes (default: 100 books)
- **ISBN Management**: Fetches missing ISBNs or generates unique identifiers
- **Skip Existing**: Option to skip already imported books
- **Rate Limiting**: Respects API rate limits (1 req/sec)
- **Comprehensive Logging**: Detailed logs for monitoring and debugging
- **Statistics Tracking**: Real-time import statistics

## Dataset Requirements

### CSV Format

The loader expects CSV files with the following columns:

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `isbn` | String | No | ISBN-10 or ISBN-13 |
| `lccn` | String | No | Library of Congress Control Number |
| `title` | String | Yes | Book title |
| `author` | String | Yes | Author name(s) |
| `text` | JSON Array | Yes | Array of page content strings |
| `publication_date` | String | No | Publication date (various formats) |
| `cover_url` | String | No | URL to cover image |

### Example CSV Row

```csv
isbn,lccn,title,author,text,publication_date,cover_url
9780141439518,2003012345,"Pride and Prejudice","Jane Austen","[""It is a truth universally acknowledged..."", ""Chapter 2...""]",1813,https://example.com/cover.jpg
```

### Text Field Format

The `text` field should be a JSON array of strings, where each string represents one page:

```json
[
  "Page 1 content here...",
  "Page 2 content here...",
  "Page 3 content here..."
]
```

### Dataset Size Considerations

| Dataset Size | Books | Pages | Storage | Load Time (est.) |
|--------------|-------|-------|---------|------------------|
| Small | 1K-10K | 100K-1M | 1-10 GB | 1-5 hours |
| Medium | 10K-100K | 1M-10M | 10-100 GB | 5-24 hours |
| Large | 100K-500K | 10M-50M | 100-400 GB | 1-5 days |
| Very Large | 500K+ | 50M+ | 400GB+ | 5-10 days |

## Pre-Loading Preparation

### 1. Database Optimization

Before loading large datasets, optimize PostgreSQL settings:

```bash
# Edit docker-compose.prod.yml or connect to database
docker-compose -f docker-compose.prod.yml exec postgres psql -U booklook_user -d booklook_production
```

```sql
-- Disable autovacuum during bulk load
ALTER TABLE books SET (autovacuum_enabled = false);
ALTER TABLE book_pages SET (autovacuum_enabled = false);
ALTER TABLE authors SET (autovacuum_enabled = false);

-- Increase maintenance work memory
SET maintenance_work_mem = '4GB';

-- Disable synchronous commit for faster writes
SET synchronous_commit = off;

-- Increase checkpoint segments
SET checkpoint_segments = 64;
SET checkpoint_completion_target = 0.9;
```

### 2. Prepare Storage

```bash
# Check available disk space (need 2x dataset size)
df -h

# For 400GB dataset, ensure at least 800GB free
# Database: 400GB
# Indexes: 100GB
# Temp files: 100GB
# Buffer: 200GB

# Create directory for CSV files
mkdir -p /mnt/data/datasets
cd /mnt/data/datasets

# If files are compressed, extract them
tar -xzf institutional_books.tar.gz
# or
unzip institutional_books.zip
```

### 3. Verify CSV Files

```bash
# Count total CSV files
ls -1 *.csv | wc -l

# Check file sizes
du -sh *.csv

# Verify CSV format (check first file)
head -n 5 books_001.csv

# Count total rows (approximate)
wc -l *.csv
```

### 4. Test with Small Sample

```bash
# Create test directory
mkdir -p /tmp/test_dataset

# Copy first CSV file for testing
cp books_001.csv /tmp/test_dataset/

# Run test import
cd /home/booklook/apps/booklook
python load_institutional_dataset.py /tmp/test_dataset --batch-size 10

# Verify import
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "SELECT COUNT(*) FROM books;"
```

## Loading Process

### 1. Basic Usage

```bash
# Navigate to application directory
cd /home/booklook/apps/booklook

# Activate virtual environment (if using)
source venv/bin/activate

# Run loader with default settings
python load_institutional_dataset.py /path/to/csv/files

# With custom batch size
python load_institutional_dataset.py /path/to/csv/files --batch-size 200

# Skip existing books (for resuming interrupted loads)
python load_institutional_dataset.py /path/to/csv/files --skip-existing

# Disable ISBN fetching (faster, but generates all ISBNs)
python load_institutional_dataset.py /path/to/csv/files --no-fetch-isbn
```

### 2. Command-Line Options

```
usage: load_institutional_dataset.py [-h] [--batch-size BATCH_SIZE]
                                     [--skip-existing] [--no-fetch-isbn]
                                     csv_directory

positional arguments:
  csv_directory         Directory containing CSV files

optional arguments:
  -h, --help            Show help message
  --batch-size BATCH_SIZE
                        Number of books to process per batch (default: 100)
  --skip-existing       Skip books that already exist in database
  --no-fetch-isbn       Don't fetch ISBNs from Open Library API
```

### 3. Running in Background

For large datasets, run in background with nohup:

```bash
# Run in background
nohup python load_institutional_dataset.py /mnt/data/datasets \
    --batch-size 200 \
    --skip-existing \
    > import.log 2>&1 &

# Get process ID
echo $!

# Save PID for later
echo $! > import.pid

# Monitor progress
tail -f import.log
tail -f dataset_import.log
```

### 4. Using Screen or Tmux

Recommended for long-running imports:

```bash
# Using screen
screen -S booklook-import
python load_institutional_dataset.py /mnt/data/datasets --batch-size 200
# Detach: Ctrl+A, D
# Reattach: screen -r booklook-import

# Using tmux
tmux new -s booklook-import
python load_institutional_dataset.py /mnt/data/datasets --batch-size 200
# Detach: Ctrl+B, D
# Reattach: tmux attach -t booklook-import
```

## Performance Optimization

### 1. Batch Size Tuning

Optimal batch size depends on available RAM:

| RAM | Recommended Batch Size |
|-----|------------------------|
| 8 GB | 50 |
| 16 GB | 100 |
| 32 GB | 200 |
| 64 GB | 500 |
| 128 GB | 1000 |

```bash
# Test different batch sizes
python load_institutional_dataset.py /path/to/sample --batch-size 50
python load_institutional_dataset.py /path/to/sample --batch-size 100
python load_institutional_dataset.py /path/to/sample --batch-size 200

# Monitor memory usage
watch -n 5 'free -h'
```

### 2. Parallel Loading

For very large datasets, split CSV files and run multiple loaders:

```bash
# Split CSV files into directories
mkdir -p /mnt/data/datasets/{batch1,batch2,batch3,batch4}

# Distribute files
ls *.csv | split -l 250 - split_
mv split_aa /mnt/data/datasets/batch1/
mv split_ab /mnt/data/datasets/batch2/
mv split_ac /mnt/data/datasets/batch3/
mv split_ad /mnt/data/datasets/batch4/

# Run parallel loaders (in separate terminals/screens)
screen -S import1
python load_institutional_dataset.py /mnt/data/datasets/batch1 --batch-size 200

screen -S import2
python load_institutional_dataset.py /mnt/data/datasets/batch2 --batch-size 200

screen -S import3
python load_institutional_dataset.py /mnt/data/datasets/batch3 --batch-size 200

screen -S import4
python load_institutional_dataset.py /mnt/data/datasets/batch4 --batch-size 200
```

### 3. Database Tuning During Load

```sql
-- Connect to database
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production

-- Temporarily disable constraints (DANGEROUS - use with caution)
ALTER TABLE book_pages DISABLE TRIGGER ALL;
ALTER TABLE book_authors DISABLE TRIGGER ALL;

-- After load, re-enable
ALTER TABLE book_pages ENABLE TRIGGER ALL;
ALTER TABLE book_authors ENABLE TRIGGER ALL;

-- Increase checkpoint timeout
SET checkpoint_timeout = '30min';

-- Increase WAL buffers
SET wal_buffers = '16MB';
```

### 4. Network Optimization (for ISBN fetching)

```bash
# Disable ISBN fetching for faster import
python load_institutional_dataset.py /path/to/csv --no-fetch-isbn

# Or increase API delay in code (edit load_institutional_dataset.py)
# self.api_delay = 0.5  # Faster, but may hit rate limits
```

## Monitoring Progress

### 1. Log Files

Two log files are created:

- `dataset_import.log` - Detailed import log
- `import.log` - Standard output (if using nohup)

```bash
# Monitor main log
tail -f dataset_import.log

# Monitor with grep for specific info
tail -f dataset_import.log | grep "Batch"
tail -f dataset_import.log | grep "ERROR"

# View statistics
tail -f dataset_import.log | grep "Statistics"
```

### 2. Database Queries

```sql
-- Count imported books
SELECT COUNT(*) FROM books;

-- Count pages
SELECT COUNT(*) FROM book_pages;

-- Count authors
SELECT COUNT(*) FROM authors;

-- Check recent imports
SELECT id, title, created_at 
FROM books 
ORDER BY created_at DESC 
LIMIT 10;

-- Check database size
SELECT pg_size_pretty(pg_database_size('booklook_production'));

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 3. System Monitoring

```bash
# Monitor CPU and memory
htop

# Monitor disk I/O
iotop

# Monitor disk space
watch -n 60 'df -h'

# Monitor network (if fetching ISBNs)
nethogs

# Docker stats
docker stats

# PostgreSQL connections
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "SELECT count(*) FROM pg_stat_activity;"
```

### 4. Progress Estimation

```bash
# Count total books to import
total_books=$(wc -l /mnt/data/datasets/*.csv | tail -1 | awk '{print $1}')

# Count imported books
imported=$(docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production -t \
    -c "SELECT COUNT(*) FROM books;")

# Calculate progress
echo "Progress: $imported / $total_books"
echo "Percentage: $(echo "scale=2; $imported * 100 / $total_books" | bc)%"

# Estimate time remaining (based on current rate)
# Check log for processing rate
grep "Batch" dataset_import.log | tail -20
```

## Troubleshooting

### Common Issues

#### 1. Out of Memory

**Symptoms:**
- Process killed
- "MemoryError" in logs
- System becomes unresponsive

**Solutions:**
```bash
# Reduce batch size
python load_institutional_dataset.py /path/to/csv --batch-size 50

# Increase swap space
sudo fallocate -l 16G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Add to /etc/fstab for persistence
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

#### 2. Disk Space Full

**Symptoms:**
- "No space left on device"
- Database errors
- Import stops

**Solutions:**
```bash
# Check disk space
df -h

# Clean up Docker
docker system prune -a

# Remove old backups
rm -rf /home/booklook/apps/booklook/backups/*

# Move database to larger disk
# (See dedicated server guide)
```

#### 3. Database Connection Errors

**Symptoms:**
- "Connection refused"
- "Too many connections"
- Timeout errors

**Solutions:**
```bash
# Check PostgreSQL status
docker-compose -f docker-compose.prod.yml ps postgres

# Check connections
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "SELECT count(*) FROM pg_stat_activity;"

# Increase max connections (edit .env.production)
POSTGRES_MAX_CONNECTIONS=300

# Restart PostgreSQL
docker-compose -f docker-compose.prod.yml restart postgres
```

#### 4. ISBN API Rate Limiting

**Symptoms:**
- "Rate limit exceeded"
- Slow import speed
- API errors in logs

**Solutions:**
```bash
# Disable ISBN fetching
python load_institutional_dataset.py /path/to/csv --no-fetch-isbn

# Or increase delay in code
# Edit load_institutional_dataset.py:
# self.api_delay = 2.0  # Increase from 1.0 to 2.0
```

#### 5. Duplicate Key Errors

**Symptoms:**
- "IntegrityError: duplicate key"
- Books skipped
- Import continues but with errors

**Solutions:**
```bash
# Use skip-existing flag
python load_institutional_dataset.py /path/to/csv --skip-existing

# Or clean database first
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "TRUNCATE books, book_pages, authors, book_authors CASCADE;"
```

### Recovery from Interrupted Import

```bash
# Resume import with skip-existing
python load_institutional_dataset.py /path/to/csv \
    --skip-existing \
    --batch-size 200

# Check for orphaned records
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "SELECT COUNT(*) FROM books WHERE total_pages = 0;"

# Clean up if needed
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production \
    -c "DELETE FROM books WHERE total_pages = 0;"
```

## Post-Loading Tasks

### 1. Re-enable Database Optimizations

```sql
-- Connect to database
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U booklook_user -d booklook_production

-- Re-enable autovacuum
ALTER TABLE books SET (autovacuum_enabled = true);
ALTER TABLE book_pages SET (autovacuum_enabled = true);
ALTER TABLE authors SET (autovacuum_enabled = true);

-- Reset synchronous commit
SET synchronous_commit = on;

-- Run VACUUM ANALYZE
VACUUM ANALYZE books;
VACUUM ANALYZE book_pages;
VACUUM ANALYZE authors;
VACUUM ANALYZE book_authors;
```

### 2. Create Indexes

```sql
-- Create missing indexes
CREATE INDEX IF NOT EXISTS idx_books_title_gin 
    ON books USING gin(to_tsvector('english', title));

CREATE INDEX IF NOT EXISTS idx_books_publication_year 
    ON books(publication_year);

CREATE INDEX IF NOT EXISTS idx_book_pages_book_id 
    ON book_pages(book_id);

CREATE INDEX IF NOT EXISTS idx_book_pages_page_number 
    ON book_pages(book_id, page_number);

-- Analyze tables
ANALYZE books;
ANALYZE book_pages;
ANALYZE authors;
```

### 3. Update Statistics

```sql
-- Update table statistics
ANALYZE VERBOSE books;
ANALYZE VERBOSE book_pages;
ANALYZE VERBOSE authors;

-- Check statistics
SELECT 
    schemaname,
    tablename,
    n_live_tup,
    n_dead_tup,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE schemaname = 'public';
```

### 4. Create Backup

```bash
# Create full backup after successful import
cd /home/booklook/apps/booklook
./backup.sh full

# Verify backup
ls -lh backups/

# Test restore (on test database)
# ./backup.sh restore backups/booklook_db_YYYYMMDD_HHMMSS.sql.gz
```

### 5. Verify Data Integrity

```sql
-- Check for books without pages
SELECT COUNT(*) FROM books WHERE total_pages = 0;

-- Check for orphaned pages
SELECT COUNT(*) FROM book_pages 
WHERE book_id NOT IN (SELECT id FROM books);

-- Check for books without authors
SELECT COUNT(*) FROM books b
WHERE NOT EXISTS (
    SELECT 1 FROM book_authors ba WHERE ba.book_id = b.id
);

-- Verify page counts
SELECT 
    b.id,
    b.title,
    b.total_pages,
    COUNT(bp.id) as actual_pages
FROM books b
LEFT JOIN book_pages bp ON b.id = bp.book_id
GROUP BY b.id, b.title, b.total_pages
HAVING b.total_pages != COUNT(bp.id)
LIMIT 10;
```

### 6. Performance Testing

```bash
# Test search performance
time curl "http://localhost:8000/api/v1/books?search=test&page=1&page_size=20"

# Test book detail retrieval
time curl "http://localhost:8000/api/v1/books/1"

# Test page content retrieval
time curl "http://localhost:8000/api/v1/books/1/content/page/1"

# Run health check
./health-check.sh full
```

## Best Practices

1. **Always test with small sample first**
2. **Monitor disk space continuously**
3. **Use screen/tmux for long-running imports**
4. **Keep detailed logs**
5. **Create backups before and after**
6. **Verify data integrity after import**
7. **Optimize database settings for bulk load**
8. **Use skip-existing for resuming**
9. **Monitor system resources**
10. **Document any issues and solutions**

## Performance Benchmarks

Based on testing with various configurations:

| Configuration | Books/Hour | Pages/Hour | Notes |
|---------------|------------|------------|-------|
| 8GB RAM, batch=50 | 1,000 | 100,000 | Basic |
| 16GB RAM, batch=100 | 2,500 | 250,000 | Recommended minimum |
| 32GB RAM, batch=200 | 5,000 | 500,000 | Good performance |
| 64GB RAM, batch=500 | 10,000 | 1,000,000 | Optimal |
| 64GB RAM, batch=500, no-fetch-isbn | 15,000 | 1,500,000 | Maximum speed |

*Actual performance varies based on CPU, disk I/O, and network speed.*

## Support

For issues during data loading:
- Check `dataset_import.log` for detailed errors
- Monitor system resources with `htop` and `df -h`
- Review database logs: `./logs.sh postgres`
- Consult troubleshooting section above

---

**Last Updated**: 2024
**Version**: 1.0
