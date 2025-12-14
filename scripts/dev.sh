#!/bin/bash

# Development script for Hackathon Todo
# Usage: ./scripts/dev.sh [backend|frontend|all]

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Start database services
start_db() {
    log_info "Starting database services..."
    docker-compose up -d postgres redis
    log_info "Waiting for services to be healthy..."
    sleep 5
}

# Start backend
start_backend() {
    log_info "Starting backend..."
    cd backend

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv venv
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Install dependencies
    log_info "Installing dependencies..."
    pip install -r requirements.txt

    # Copy .env if it doesn't exist
    if [ ! -f ".env" ]; then
        log_warn ".env file not found. Copying from .env.example..."
        cp .env.example .env
    fi

    # Run migrations
    log_info "Running migrations..."
    alembic upgrade head 2>/dev/null || log_warn "Migrations skipped (may need manual setup)"

    # Start server
    log_info "Starting FastAPI server on http://localhost:8000"
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
}

# Start frontend
start_frontend() {
    log_info "Starting frontend..."
    cd frontend

    # Install dependencies if node_modules doesn't exist
    if [ ! -d "node_modules" ]; then
        log_info "Installing dependencies..."
        npm install
    fi

    # Copy .env if it doesn't exist
    if [ ! -f ".env" ]; then
        log_warn ".env file not found. Copying from .env.example..."
        cp .env.example .env
    fi

    # Start server
    log_info "Starting Next.js server on http://localhost:3000"
    npm run dev
}

# Main
case "${1:-all}" in
    backend)
        check_docker
        start_db
        start_backend
        ;;
    frontend)
        start_frontend
        ;;
    db)
        check_docker
        start_db
        log_info "Database services are running."
        ;;
    all)
        check_docker
        start_db
        log_info "Starting all services..."
        log_info "Run './scripts/dev.sh backend' in one terminal"
        log_info "Run './scripts/dev.sh frontend' in another terminal"
        ;;
    docker)
        check_docker
        log_info "Starting all services with Docker Compose..."
        docker-compose up --build
        ;;
    *)
        echo "Usage: $0 [backend|frontend|db|all|docker]"
        echo ""
        echo "Commands:"
        echo "  backend   - Start backend server (requires db)"
        echo "  frontend  - Start frontend server"
        echo "  db        - Start database services only"
        echo "  all       - Start database and show instructions"
        echo "  docker    - Start all services with Docker Compose"
        exit 1
        ;;
esac
