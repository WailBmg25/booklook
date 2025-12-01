#!/bin/bash

# BookLook Deployment Script
# This script handles the deployment of the BookLook application

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

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    print_info "Checking requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check environment file
    if [ ! -f "$ENV_FILE" ]; then
        print_error "Environment file $ENV_FILE not found."
        print_info "Please copy .env.production.example to $ENV_FILE and configure it."
        exit 1
    fi
    
    print_success "All requirements met."
}

build_images() {
    print_info "Building Docker images..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" build --no-cache
    print_success "Images built successfully."
}

start_services() {
    print_info "Starting services..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" up -d
    print_success "Services started successfully."
}

stop_services() {
    print_info "Stopping services..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" down
    print_success "Services stopped successfully."
}

restart_services() {
    print_info "Restarting services..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" restart
    print_success "Services restarted successfully."
}

show_status() {
    print_info "Service status:"
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" ps
}

show_logs() {
    local service=$1
    if [ -z "$service" ]; then
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" logs -f
    else
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" logs -f "$service"
    fi
}

run_migrations() {
    print_info "Running database migrations..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" exec backend bash -c "cd src && alembic upgrade head"
    if [ $? -eq 0 ]; then
        print_success "Migrations completed successfully."
    else
        print_error "Migrations failed. Check the logs for details."
        return 1
    fi
}

load_dataset() {
    local data_path=$1
    
    if [ -z "$data_path" ]; then
        print_error "Please provide path to CSV file or directory"
        print_info "Usage: ./deploy.sh load-data /path/to/csv/files"
        print_info "Or set DATASET_PATH in .env.production and use: ./deploy.sh load-data"
        return 1
    fi
    
    if [ ! -e "$data_path" ]; then
        print_error "Path does not exist: $data_path"
        return 1
    fi
    
    print_info "Loading institutional dataset from: $data_path"
    print_info "Using volume mount (no copying needed)..."
    
    # Check if path is already mounted
    local mounted_path=$(docker inspect "${PROJECT_NAME}_backend" --format='{{range .Mounts}}{{if eq .Destination "/app/dataset"}}{{.Source}}{{end}}{{end}}')
    
    if [ "$mounted_path" = "$data_path" ]; then
        print_info "Dataset already mounted at /app/dataset"
        target_path="/app/dataset"
    else
        print_warning "Dataset not mounted. Updating DATASET_PATH and restarting backend..."
        
        # Update .env.production with new path
        if grep -q "^DATASET_PATH=" "$ENV_FILE"; then
            sed -i "s|^DATASET_PATH=.*|DATASET_PATH=$data_path|" "$ENV_FILE"
        else
            echo "DATASET_PATH=$data_path" >> "$ENV_FILE"
        fi
        
        # Restart backend with new mount
        print_info "Restarting backend with dataset mount..."
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" up -d backend
        
        print_info "Waiting for backend to be ready..."
        sleep 10
        
        target_path="/app/dataset"
    fi
    
    print_info "Running data loader..."
    print_info "This may take a while depending on dataset size..."
    
    # Run the loader
    docker exec "${PROJECT_NAME}_backend" python load_institutional_dataset.py "$target_path" --skip-existing
    
    if [ $? -eq 0 ]; then
        print_success "Dataset loaded successfully!"
    else
        print_error "Dataset loading failed. Check the logs for details."
        return 1
    fi
}

health_check() {
    print_info "Performing health check..."
    
    # Check backend
    if curl -f http://localhost:8000/health &> /dev/null; then
        print_success "Backend is healthy"
    else
        print_error "Backend is not responding"
    fi
    
    # Check frontend
    if curl -f http://localhost:3000 &> /dev/null; then
        print_success "Frontend is healthy"
    else
        print_error "Frontend is not responding"
    fi
}

show_help() {
    cat << EOF
BookLook Deployment Script

Usage: ./deploy.sh [COMMAND] [OPTIONS]

Commands:
    start              Start all services
    stop               Stop all services
    restart            Restart all services
    build              Build Docker images
    deploy             Build and start services (full deployment)
    status             Show service status
    logs [service]     Show logs (optionally for specific service)
    migrate            Run database migrations
    load-data <path>   Load institutional dataset from CSV files
    health             Perform health check
    pgadmin            Start with pgAdmin (database management UI)
    help               Show this help message

Examples:
    ./deploy.sh deploy                      # Full deployment
    ./deploy.sh migrate                     # Run migrations
    ./deploy.sh load-data /path/to/csvs     # Load book dataset
    ./deploy.sh pgadmin                     # Deploy with pgAdmin
    ./deploy.sh logs backend                # Show backend logs

EOF
}

# Main script
case "$1" in
    start)
        check_requirements
        start_services
        print_info "Waiting for services to be ready..."
        sleep 10
        health_check
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    build)
        check_requirements
        build_images
        ;;
    deploy)
        check_requirements
        build_images
        start_services
        print_info "Waiting for services to be ready..."
        sleep 15
        run_migrations
        health_check
        print_success "Deployment completed!"
        print_info "Access the application at:"
        print_info "  Frontend: http://localhost:3000"
        print_info "  Backend API: http://localhost:8000"
        print_info "  API Docs: http://localhost:8000/docs"
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "$2"
        ;;
    migrate)
        run_migrations
        ;;
    load-data)
        load_dataset "$2"
        ;;
    health)
        health_check
        ;;
    pgadmin)
        check_requirements
        print_info "Starting services with pgAdmin..."
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" --profile with-pgadmin up -d
        print_success "Services started with pgAdmin!"
        print_info "Access pgAdmin at: http://localhost:5050"
        print_info "Default credentials:"
        print_info "  Email: admin@booklook.com"
        print_info "  Password: (check your .env.production file)"
        print_info ""
        print_info "To connect to PostgreSQL in pgAdmin:"
        print_info "  Host: postgres"
        print_info "  Port: 5432"
        print_info "  Database: book_library"
        print_info "  Username: (check your .env.production file)"
        print_info "  Password: (check your .env.production file)"
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
