#!/bin/bash
set -e

# ============================================
# IA Trading - Deploy Script for IONOS VPS
# ============================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  IA Trading - Deploy Script${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Copy .env.production.example to .env and configure it:"
    echo "  cp .env.production.example .env"
    echo "  nano .env"
    exit 1
fi

# Pull latest changes
echo -e "${YELLOW}Pulling latest changes...${NC}"
git pull origin master

# Build and start containers
echo -e "${YELLOW}Building and starting containers...${NC}"
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d

# Wait for services
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 10

# Check health
echo -e "${YELLOW}Checking API health...${NC}"
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo -e "${GREEN}API is healthy!${NC}"
else
    echo -e "${RED}API health check failed!${NC}"
    echo "Checking logs..."
    docker compose -f docker-compose.prod.yml logs --tail=50 api
    exit 1
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deploy completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Useful commands:"
echo "  docker compose -f docker-compose.prod.yml logs -f api    # View API logs"
echo "  docker compose -f docker-compose.prod.yml logs -f db     # View DB logs"
echo "  docker compose -f docker-compose.prod.yml restart api    # Restart API"
echo "  docker compose -f docker-compose.prod.yml down           # Stop all"
