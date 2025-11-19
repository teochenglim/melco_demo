#!/bin/bash

# Casino Gaming Loyalty Demo - Quick Start Script
# This script handles the complete setup and execution of the demo

set -e  # Exit on error

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}🎰  Casino Gaming Loyalty Demo${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_step() {
    echo -e "${YELLOW}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

wait_for_port() {
    local host=$1
    local port=$2
    local service=$3
    local max_attempts=30
    local attempt=1

    print_step "Waiting for $service on port $port..."

    while [ $attempt -le $max_attempts ]; do
        if nc -z $host $port 2>/dev/null || timeout 1 bash -c "echo > /dev/tcp/$host/$port" 2>/dev/null; then
            print_success "$service is ready"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    print_error "$service failed to start on port $port"
    return 1
}

check_prerequisites() {
    print_step "Checking prerequisites..."

    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    print_success "All prerequisites are installed (Docker + Docker Compose only!)"
}

start_services() {
    print_step "Starting Docker services..."
    docker-compose up -d

    # Wait for critical services to be accessible
    wait_for_port localhost 19092 "Redpanda"
    wait_for_port localhost 4566 "RisingWave"
    wait_for_port localhost 8501 "Streamlit"

    print_success "All services started"
}

wait_for_init() {
    print_step "Waiting for initialization (data-generator handles Kafka topic + RisingWave schema)..."

    # Wait for data-generator to be healthy (it runs init then starts API)
    local max_attempts=60
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:8000/health 2>/dev/null | grep -q "ok" || \
           curl -s http://localhost:8000/status 2>/dev/null | grep -q "running"; then
            print_success "All services initialized and ready"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    print_error "Timeout waiting for initialization"
    echo "Data generator logs:"
    docker logs casino-data-generator --tail 50
    return 1
}

start_streamlit() {
    print_step "Starting Streamlit dashboard..."

    # Ensure streamlit container is running
    if ! docker ps | grep -q streamlit-dashboard; then
        docker start streamlit-dashboard 2>/dev/null || docker-compose up -d streamlit
    fi

    sleep 3
    print_success "Streamlit dashboard is running"
}

open_dashboard() {
    print_step "Opening dashboard in browser..."

    if command -v open &> /dev/null; then
        # macOS
        open http://localhost:8501
    elif command -v xdg-open &> /dev/null; then
        # Linux
        xdg-open http://localhost:8501
    else
        echo -e "${YELLOW}Please open http://localhost:8501 in your browser${NC}"
    fi
}

show_status() {
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}🎉  Demo is running!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BLUE}📍 Access Points:${NC}"
    echo -e "  ${YELLOW}Streamlit Dashboard:${NC}  http://localhost:8501"
    echo -e "  ${YELLOW}Redpanda Console:${NC}     http://localhost:8080"
    echo -e "  ${YELLOW}RisingWave (psql):${NC}    psql -h localhost -p 4566 -d dev -U root"
    echo ""
    echo -e "${BLUE}📊 Container Status:${NC}"
    docker-compose ps
    echo ""
}

inject_data() {
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}💉  Starting data injection (5 events/sec)${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  Keep this terminal open to continue generating data${NC}"
    echo -e "${YELLOW}⚠️  Press Ctrl+C to stop${NC}"
    echo ""

    # Wait for data generator to auto-start (FastAPI auto-starts at 5 events/sec)
    print_step "Waiting for data generator to auto-start..."
    sleep 5

    # Verify generator is running via REST API
    if curl -s http://localhost:8000/status | grep -q '"running":true'; then
        print_success "Data generator is running at 5 events/sec (auto-started)"
    else
        print_error "Data generator not running. Attempting manual start..."
        curl -s -X POST http://localhost:8000/start | jq '.' || echo "Failed to start generator"
    fi

    echo ""
    echo -e "${BLUE}To control the generator:${NC}"
    echo -e "  ${YELLOW}make inject-rate${NC}   - Check current rate"
    echo -e "  ${YELLOW}make inject-fast${NC}   - Increase to 10 events/sec"
    echo -e "  ${YELLOW}make inject-slow${NC}   - Decrease to 2 events/sec"
    echo -e "  ${YELLOW}make inject-stop${NC}   - Stop generation"
    echo ""
    echo -e "${GREEN}Press Ctrl+C to exit this script (generator will keep running)${NC}"

    # Keep script running to show status
    while true; do
        sleep 30
    done
}

cleanup() {
    echo ""
    print_step "Cleaning up..."
    print_success "Demo stopped. Containers are still running."
    echo ""
    echo -e "${BLUE}To stop all services, run:${NC} docker-compose down"
    echo -e "${BLUE}To restart data injection:${NC} make inject"
}

# Main execution
main() {
    print_header

    # Parse command line arguments
    case "${1:-}" in
        stop)
            print_step "Stopping all services..."
            docker-compose down
            print_success "All services stopped"
            exit 0
            ;;
        clean)
            print_step "Removing all containers and volumes..."
            docker-compose down -v
            print_success "Cleanup complete"
            exit 0
            ;;
        status)
            show_status
            exit 0
            ;;
        restart)
            print_step "Restarting services..."
            docker-compose restart
            sleep 5
            show_status
            exit 0
            ;;
        help|--help|-h)
            echo "Usage: ./run-demo.sh [command]"
            echo ""
            echo "Commands:"
            echo "  (no args)   Start the complete demo"
            echo "  stop        Stop all services"
            echo "  clean       Remove all containers and volumes"
            echo "  status      Show current status"
            echo "  restart     Restart all services"
            echo "  help        Show this help message"
            exit 0
            ;;
    esac

    # Trap Ctrl+C for clean exit
    trap cleanup EXIT INT TERM

    # Execute setup steps
    check_prerequisites
    start_services
    wait_for_init
    start_streamlit
    sleep 2
    show_status
    open_dashboard

    # Start data injection
    inject_data
}

# Run main function
main "$@"
