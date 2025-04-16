#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Setting up development environment...${NC}"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js is not installed. Please install Node.js first.${NC}"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Create necessary directories
echo -e "${YELLOW}Creating required directories...${NC}"
mkdir -p uploads logs

# Copy environment files
echo -e "${YELLOW}Setting up environment files...${NC}"
if [ ! -f "back-end/.env" ]; then
    cp back-end/.env.development back-end/.env
    echo -e "${GREEN}Created .env file from .env.development${NC}"
else
    echo -e "${YELLOW}Using existing .env file${NC}"
fi

# Install backend dependencies
echo -e "${YELLOW}Installing backend dependencies...${NC}"
cd back-end
npm install
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install backend dependencies${NC}"
    exit 1
fi

# Install frontend dependencies
echo -e "${YELLOW}Installing frontend dependencies...${NC}"
cd ../front-end
npm install
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install frontend dependencies${NC}"
    exit 1
fi

cd ..

# Make deploy script executable
chmod +x deploy.sh

# Set up git hooks
echo -e "${YELLOW}Setting up git hooks...${NC}"
if [ -d ".git" ]; then
    cp scripts/pre-commit.sh .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
    echo -e "${GREEN}Git hooks installed${NC}"
fi

# Start development environment
echo -e "${YELLOW}Starting development environment...${NC}"
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 10

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
cd back-end
npm run migrate
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to run database migrations${NC}"
    exit 1
fi

# Seed database with sample data
echo -e "${YELLOW}Seeding database with sample data...${NC}"
npm run seed
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to seed database${NC}"
    exit 1
fi

cd ..

echo -e "${GREEN}Development environment setup complete!${NC}"
echo -e "${YELLOW}You can now run the following commands:${NC}"
echo -e "  ${GREEN}npm run dev${NC} - Start the backend development server"
echo -e "  ${GREEN}cd front-end && npm start${NC} - Start the frontend development server"
echo -e "  ${GREEN}./deploy.sh${NC} - Deploy to production environment"
echo -e "\n${YELLOW}Access the application at:${NC}"
echo -e "  Frontend: ${GREEN}http://localhost:3000${NC}"
echo -e "  Backend API: ${GREEN}http://localhost:5000${NC}"
echo -e "  API Documentation: ${GREEN}http://localhost:5000/api-docs${NC}"

# Monitor logs
echo -e "\n${YELLOW}Monitoring Docker logs... Press Ctrl+C to stop${NC}"
docker-compose -f docker-compose.dev.yml logs -f