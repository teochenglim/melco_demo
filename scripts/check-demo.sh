#!/bin/bash

# Quick health check script for the casino demo

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🔍 Casino Demo Health Check${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check Docker
echo -e "${YELLOW}▶ Checking Docker...${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker is installed${NC}"
else
    echo -e "${RED}✗ Docker is NOT installed${NC}"
    exit 1
fi

# Check containers
echo ""
echo -e "${YELLOW}▶ Container Status:${NC}"
docker-compose ps

# Check if containers are running
echo ""
REDPANDA=$(docker ps --filter "name=redpanda" --format "{{.Status}}" | grep -c "Up")
RISINGWAVE=$(docker ps --filter "name=risingwave" --format "{{.Status}}" | grep -c "Up")
STREAMLIT=$(docker ps --filter "name=streamlit" --format "{{.Status}}" | grep -c "Up")

if [ "$REDPANDA" -eq 1 ]; then
    echo -e "${GREEN}✓ Redpanda is running${NC}"
else
    echo -e "${RED}✗ Redpanda is NOT running${NC}"
fi

if [ "$RISINGWAVE" -eq 1 ]; then
    echo -e "${GREEN}✓ RisingWave is running${NC}"
else
    echo -e "${RED}✗ RisingWave is NOT running${NC}"
fi

if [ "$STREAMLIT" -eq 1 ]; then
    echo -e "${GREEN}✓ Streamlit is running${NC}"
else
    echo -e "${RED}✗ Streamlit is NOT running${NC}"
fi

# Check ports
echo ""
echo -e "${YELLOW}▶ Port Accessibility:${NC}"

check_port() {
    local port=$1
    local name=$2
    local url=$3

    if nc -z localhost $port 2>/dev/null || curl -s -o /dev/null -w "%{http_code}" $url | grep -q "200"; then
        echo -e "${GREEN}✓ $name (port $port) - ${url}${NC}"
        return 0
    else
        echo -e "${RED}✗ $name (port $port) is NOT accessible${NC}"
        return 1
    fi
}

check_port 19092 "Redpanda Kafka" "localhost:19092"
check_port 4566 "RisingWave" "localhost:4566"
check_port 8501 "Streamlit" "http://localhost:8501"
check_port 8080 "Redpanda Console" "http://localhost:8080"

# Check RisingWave data
echo ""
echo -e "${YELLOW}▶ Checking RisingWave Data:${NC}"

DATA_CHECK=$(docker exec risingwave psql -h localhost -p 4566 -d dev -U root -t -c "SELECT COUNT(*) FROM member_daily_summary;" 2>/dev/null | tr -d ' ')

if [ ! -z "$DATA_CHECK" ] && [ "$DATA_CHECK" -ge 0 ]; then
    echo -e "${GREEN}✓ RisingWave is accessible and has $DATA_CHECK members${NC}"
else
    echo -e "${YELLOW}⚠ RisingWave connection issue or no data yet${NC}"
fi

# Summary
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📍 Quick Actions:${NC}"
echo ""
echo -e "  ${YELLOW}Start demo:${NC}        ./run-demo.sh"
echo -e "  ${YELLOW}Stop demo:${NC}         ./run-demo.sh stop"
echo -e "  ${YELLOW}View logs:${NC}         docker-compose logs -f"
echo -e "  ${YELLOW}Dashboard:${NC}         http://localhost:8501"
echo -e "  ${YELLOW}Redpanda Console:${NC}  http://localhost:8080"
echo ""
