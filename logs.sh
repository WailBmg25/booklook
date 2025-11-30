#!/bin/bash

# BookLook Logs Viewer Script
# This script provides easy access to service logs

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

# Functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_logs() {
    local service=$1
    local lines=${2:-100}
    local follow=${3:-false}
    
    if [ "$follow" = "true" ]; then
        print_info "Following logs for $service (Ctrl+C to exit)..."
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" logs -f --tail="$lines" "$service"
    else
        print_info "Showing last $lines lines for $service..."
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" logs --tail="$lines" "$service"
    fi
}

show_all_logs() {
    local lines=${1:-100}
    local follow=${2:-false}
    
    if [ "$follow" = "true" ]; then
        print_info "Following all service logs (Ctrl+C to exit)..."
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" logs -f --tail="$lines"
    else
        print_info "Showing last $lines lines for all services..."
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" logs --tail="$lines"
    fi
}

show_errors() {
    local service=$1
    
    if [ -z "$service" ]; then
        print_info "Showing errors from all services..."
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" logs | grep -i "error\|exception\|failed\|fatal"
    else
        print_info "Showing errors from $service..."
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" logs "$service" | grep -i "error\|exception\|failed\|fatal"
    fi
}

show_help() {
    cat << EOF
BookLook Logs Viewer Script

Usage: ./logs.sh [COMMAND] [SERVICE] [OPTIONS]

Commands:
    all [lines] [follow]    Show logs from all services
    backend [lines] [follow] Show backend logs
    frontend [lines] [follow] Show frontend logs
    postgres [lines] [follow] Show PostgreSQL logs
    redis [lines] [follow]   Show Redis logs
    nginx [lines] [follow]   Show Nginx logs
    errors [service]        Show only errors (optionally for specific service)
    help                    Show this help message

Options:
    lines       Number of lines to show (default: 100)
    follow      Set to 'follow' or 'f' to follow logs in real-time

Examples:
    ./logs.sh all                    # Show last 100 lines from all services
    ./logs.sh backend 500 follow     # Follow last 500 lines from backend
    ./logs.sh frontend 50            # Show last 50 lines from frontend
    ./logs.sh errors backend         # Show only errors from backend
    ./logs.sh postgres 200 f         # Follow last 200 lines from postgres

Available Services:
    - backend   (FastAPI application)
    - frontend  (Next.js application)
    - postgres  (PostgreSQL database)
    - redis     (Redis cache)
    - nginx     (Nginx reverse proxy)

EOF
}

# Parse follow flag
parse_follow() {
    local arg=$1
    if [ "$arg" = "follow" ] || [ "$arg" = "f" ]; then
        echo "true"
    else
        echo "false"
    fi
}

# Main script
case "$1" in
    all)
        lines=${2:-100}
        follow=$(parse_follow "$3")
        show_all_logs "$lines" "$follow"
        ;;
    backend)
        lines=${2:-100}
        follow=$(parse_follow "$3")
        show_logs "backend" "$lines" "$follow"
        ;;
    frontend)
        lines=${2:-100}
        follow=$(parse_follow "$3")
        show_logs "frontend" "$lines" "$follow"
        ;;
    postgres)
        lines=${2:-100}
        follow=$(parse_follow "$3")
        show_logs "postgres" "$lines" "$follow"
        ;;
    redis)
        lines=${2:-100}
        follow=$(parse_follow "$3")
        show_logs "redis" "$lines" "$follow"
        ;;
    nginx)
        lines=${2:-100}
        follow=$(parse_follow "$3")
        show_logs "nginx" "$lines" "$follow"
        ;;
    errors)
        show_errors "$2"
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
