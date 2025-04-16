#!/bin/bash

# Environment variables
ENV=${1:-production}
DOCKER_COMPOSE_FILE="docker-compose.yml"
ENV_FILE="back-end/.env.${ENV}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if environment file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: Environment file $ENV_FILE not found${NC}"
    exit 1
fi

echo -e "${YELLOW}Starting deployment for ${ENV} environment...${NC}"

# Load environment variables
set -a
source "$ENV_FILE"
set +a

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check required tools
for cmd in docker docker-compose; do
    if ! command_exists "$cmd"; then
        echo -e "${RED}Error: $cmd is required but not installed${NC}"
        exit 1
    fi
done

# Function to handle errors
handle_error() {
    echo -e "${RED}Error: $1${NC}"
    exit 1
}

# Create necessary directories
echo -e "${YELLOW}Creating required directories...${NC}"
mkdir -p uploads logs backup

# Backup database if in production
if [ "$ENV" = "production" ]; then
    echo -e "${YELLOW}Creating database backup...${NC}"
    docker-compose exec -T mongodb mongodump --uri="$MONGODB_URI" --out="/backup/$(date +%Y%m%d)" || handle_error "Database backup failed"
fi

# Pull latest images
echo -e "${YELLOW}Pulling latest Docker images...${NC}"
docker-compose -f "$DOCKER_COMPOSE_FILE" pull || handle_error "Failed to pull Docker images"

# Stop and remove existing containers
echo -e "${YELLOW}Stopping existing containers...${NC}"
docker-compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans

# Start new containers
echo -e "${YELLOW}Starting new containers...${NC}"
docker-compose -f "$DOCKER_COMPOSE_FILE" up -d || handle_error "Failed to start containers"

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 10

# Run database migrations if needed
echo -e "${YELLOW}Running database migrations...${NC}"
docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T backend npm run migrate || handle_error "Database migration failed"

# Clear cache if Redis is used
if [ -n "$REDIS_URL" ]; then
    echo -e "${YELLOW}Clearing cache...${NC}"
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T backend npm run cache:clear || echo -e "${YELLOW}Warning: Cache clear failed${NC}"
fi

# Verify deployment
echo -e "${YELLOW}Verifying deployment...${NC}"
HEALTH_CHECK_URL="http://localhost:5000/api/health"
MAX_RETRIES=5
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s "$HEALTH_CHECK_URL" | grep -q "ok"; then
        echo -e "${GREEN}Deployment successful!${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        handle_error "Health check failed after $MAX_RETRIES attempts"
    fi
    echo -e "${YELLOW}Waiting for service to be ready... (Attempt $RETRY_COUNT/$MAX_RETRIES)${NC}"
    sleep 5
done

# Print container status
echo -e "${YELLOW}Container status:${NC}"
docker-compose -f "$DOCKER_COMPOSE_FILE" ps

# Monitor logs
echo -e "${YELLOW}Monitoring logs... Press Ctrl+C to stop${NC}"
docker-compose -f "$DOCKER_COMPOSE_FILE" logs -f

# Function to handle cleanup on script exit
cleanup() {
    echo -e "\n${YELLOW}Deployment script terminated${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep script running to maintain log output
wait