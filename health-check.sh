#!/bin/bash

# BookLook Health Check Script
# This script checks the health of all services

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

# Detect docker compose command
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Load environment variables
if [ -f "$ENV_FILE" ]; then
    export $(cat "$ENV_FILE" | grep -v '^#' | xargs)
fi

# Default ports
BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-3000}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
REDIS_PORT=${REDIS_PORT:-6379}

# Functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

check_container() {
    local service=$1
    local container_name="${PROJECT_NAME}-${service}-1"
    
    if docker ps --format '{{.Names}}' | grep -q "$service"; then
        local status=$(docker inspect --format='{{.State.Status}}' $(docker ps -qf "name=$service") 2>/dev/null)
        if [ "$status" = "running" ]; then
            print_success "$service container is running"
            return 0
        else
            print_error "$service container is not running (status: $status)"
            return 1
        fi
    else
        print_error "$service container not found"
        return 1
    fi
}

check_http_endpoint() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    
    local response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "$expected_code" ]; then
        print_success "$name is responding (HTTP $response)"
        return 0
    else
        print_error "$name is not responding correctly (HTTP $response, expected $expected_code)"
        return 1
    fi
}

check_postgres() {
    if $DOCKER_COMPOSE -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" exec -T postgres pg_isready -U "${POSTGRES_USER:-bookuser}" &>/dev/null; then
        print_success "PostgreSQL is accepting connections"
        return 0
    else
        print_error "PostgreSQL is not accepting connections"
        return 1
    fi
}

check_redis() {
    if $DOCKER_COMPOSE -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" exec -T redis redis-cli ping &>/dev/null; then
        print_success "Redis is responding"
        return 0
    else
        print_error "Redis is not responding"
        return 1
    fi
}

check_disk_space() {
    local threshold=90
    local usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$usage" -lt "$threshold" ]; then
        print_success "Disk space is healthy (${usage}% used)"
        return 0
    else
        print_warning "Disk space is running low (${usage}% used)"
        return 1
    fi
}

check_memory() {
    local threshold=90
    local usage=$(free | awk 'NR==2 {printf "%.0f", $3/$2 * 100}')
    
    if [ "$usage" -lt "$threshold" ]; then
        print_success "Memory usage is healthy (${usage}% used)"
        return 0
    else
        print_warning "Memory usage is high (${usage}% used)"
        return 1
    fi
}

full_health_check() {
    local failed=0
    
    echo ""
    print_info "=== BookLook Health Check ==="
    echo ""
    
    print_info "Checking containers..."
    check_container "postgres" || ((failed++))
    check_container "redis" || ((failed++))
    check_container "backend" || ((failed++))
    check_container "frontend" || ((failed++))
    echo ""
    
    print_info "Checking services..."
    check_postgres || ((failed++))
    check_redis || ((failed++))
    check_http_endpoint "Backend API" "http://localhost:${BACKEND_PORT}/health" || ((failed++))
    check_http_endpoint "Frontend" "http://localhost:${FRONTEND_PORT}" || ((failed++))
    echo ""
    
    print_info "Checking system resources..."
    check_disk_space || ((failed++))
    check_memory || ((failed++))
    echo ""
    
    if [ $failed -eq 0 ]; then
        print_success "=== All checks passed! ==="
        return 0
    else
        print_error "=== $failed check(s) failed ==="
        return 1
    fi
}

quick_check() {
    local failed=0
    
    check_http_endpoint "Backend" "http://localhost:${BACKEND_PORT}/health" || ((failed++))
    check_http_endpoint "Frontend" "http://localhost:${FRONTEND_PORT}" || ((failed++))
    
    if [ $failed -eq 0 ]; then
        print_success "Quick check passed"
        return 0
    else
        print_error "Quick check failed"
        return 1
    fi
}

show_help() {
    cat << EOF
BookLook Health Check Script

Usage: ./health-check.sh [COMMAND]

Commands:
    full        Perform full health check (default)
    quick       Quick check of main endpoints
    backend     Check backend only
    frontend    Check frontend only
    database    Check database only
    redis       Check Redis only
    system      Check system resources only
    help        Show this help message

Examples:
    ./health-check.sh           # Full health check
    ./health-check.sh quick     # Quick check
    ./health-check.sh backend   # Check backend only

Exit Codes:
    0 - All checks passed
    1 - One or more checks failed

EOF
}

# Main script
case "$1" in
    full|"")
        full_health_check
        exit $?
        ;;
    quick)
        quick_check
        exit $?
        ;;
    backend)
        check_container "backend"
        check_http_endpoint "Backend API" "http://localhost:${BACKEND_PORT}/health"
        exit $?
        ;;
    frontend)
        check_container "frontend"
        check_http_endpoint "Frontend" "http://localhost:${FRONTEND_PORT}"
        exit $?
        ;;
    database)
        check_container "postgres"
        check_postgres
        exit $?
        ;;
    redis)
        check_container "redis"
        check_redis
        exit $?
        ;;
    system)
        check_disk_space
        check_memory
        exit $?
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
