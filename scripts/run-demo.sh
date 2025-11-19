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

setup_kafka() {
    print_step "Creating Kafka topic..."
    sleep 3

    docker exec redpanda rpk topic create gaming-transactions \
        --brokers=localhost:9092 \
        --partitions=3 \
        --replicas=1 2>/dev/null || true

    print_success "Kafka topic created"
}

setup_risingwave() {
    print_step "Waiting for RisingWave schema initialization..."
    sleep 5

    # Schema is automatically initialized by risingwave-init container and streamlit entrypoint
    # Just wait for it to complete
    print_success "RisingWave schema initialized by init containers"
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

    # Run generator in container (no local Python dependencies needed!)
    docker run --rm --network risingwave_casino-net \
        -v "$(pwd)/data-generator/casino_events_generator.py:/app/casino_events_generator.py:ro" \
        python:3.11-slim sh -c "pip install -q kafka-python && python /app/casino_events_generator.py --mode kafka --rate 5 --broker redpanda:9092"
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
    setup_kafka
    setup_risingwave
    start_streamlit
    sleep 2
    show_status
    open_dashboard

    # Start data injection
    inject_data
}

# Run main function
main "$@"
