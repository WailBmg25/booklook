#!/bin/bash

# BookLook Database Backup Script
# This script creates backups of the PostgreSQL database

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.production"
PROJECT_NAME="booklook"
BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Load environment variables
if [ -f "$ENV_FILE" ]; then
    export $(cat "$ENV_FILE" | grep -v '^#' | xargs)
fi

# Default values if not set
POSTGRES_USER=${POSTGRES_USER:-bookuser}
POSTGRES_DB=${POSTGRES_DB:-book_library}

# Functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        print_info "Created backup directory: $BACKUP_DIR"
    fi
}

backup_database() {
    local backup_file="$BACKUP_DIR/booklook_db_${TIMESTAMP}.sql.gz"
    
    print_info "Starting database backup..."
    print_info "Database: $POSTGRES_DB"
    print_info "User: $POSTGRES_USER"
    
    # Create backup using docker exec
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" exec -T postgres \
        pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists | gzip > "$backup_file"
    
    if [ $? -eq 0 ]; then
        local size=$(du -h "$backup_file" | cut -f1)
        print_success "Backup created successfully: $backup_file"
        print_info "Backup size: $size"
    else
        print_error "Backup failed!"
        exit 1
    fi
}

backup_volumes() {
    local backup_file="$BACKUP_DIR/booklook_volumes_${TIMESTAMP}.tar.gz"
    
    print_info "Starting volumes backup..."
    
    # Backup postgres and redis data
    tar -czf "$backup_file" -C docker postgres_data redis_data 2>/dev/null || true
    
    if [ -f "$backup_file" ]; then
        local size=$(du -h "$backup_file" | cut -f1)
        print_success "Volumes backup created: $backup_file"
        print_info "Backup size: $size"
    else
        print_warning "Volumes backup skipped (directories may not exist)"
    fi
}

restore_database() {
    local backup_file=$1
    
    if [ -z "$backup_file" ]; then
        print_error "Please specify a backup file to restore"
        print_info "Usage: ./backup.sh restore <backup_file>"
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        print_error "Backup file not found: $backup_file"
        exit 1
    fi
    
    print_warning "This will restore the database from: $backup_file"
    print_warning "All current data will be replaced!"
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        print_info "Restore cancelled."
        exit 0
    fi
    
    print_info "Restoring database..."
    
    # Restore backup using docker exec
    gunzip -c "$backup_file" | docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" exec -T postgres \
        psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
    
    if [ $? -eq 0 ]; then
        print_success "Database restored successfully!"
    else
        print_error "Restore failed!"
        exit 1
    fi
}

list_backups() {
    print_info "Available backups in $BACKUP_DIR:"
    echo ""
    
    if [ -d "$BACKUP_DIR" ] && [ "$(ls -A $BACKUP_DIR)" ]; then
        ls -lh "$BACKUP_DIR" | grep -E '\.(sql\.gz|tar\.gz)$' | awk '{print $9, "(" $5 ")", $6, $7, $8}'
    else
        print_warning "No backups found."
    fi
}

cleanup_old_backups() {
    local days=${1:-30}
    
    print_info "Cleaning up backups older than $days days..."
    
    if [ -d "$BACKUP_DIR" ]; then
        find "$BACKUP_DIR" -name "*.sql.gz" -type f -mtime +$days -delete
        find "$BACKUP_DIR" -name "*.tar.gz" -type f -mtime +$days -delete
        print_success "Cleanup completed."
    else
        print_warning "Backup directory does not exist."
    fi
}

show_help() {
    cat << EOF
BookLook Backup Script

Usage: ./backup.sh [COMMAND] [OPTIONS]

Commands:
    db              Backup database only
    volumes         Backup data volumes only
    full            Full backup (database + volumes)
    restore <file>  Restore database from backup file
    list            List available backups
    cleanup [days]  Remove backups older than N days (default: 30)
    help            Show this help message

Examples:
    ./backup.sh full                                    # Full backup
    ./backup.sh db                                      # Database only
    ./backup.sh restore backups/booklook_db_*.sql.gz   # Restore from backup
    ./backup.sh list                                    # List backups
    ./backup.sh cleanup 7                               # Remove backups older than 7 days

Backup Location: $BACKUP_DIR

EOF
}

# Main script
case "$1" in
    db)
        create_backup_dir
        backup_database
        ;;
    volumes)
        create_backup_dir
        backup_volumes
        ;;
    full)
        create_backup_dir
        backup_database
        backup_volumes
        print_success "Full backup completed!"
        ;;
    restore)
        restore_database "$2"
        ;;
    list)
        list_backups
        ;;
    cleanup)
        cleanup_old_backups "$2"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
