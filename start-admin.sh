#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Yang RAG Admin - Starting Services${NC}"
echo -e "${GREEN}========================================${NC}"

# Kill any existing processes on ports 8001 and 5173
echo -e "\n${YELLOW}Checking for existing processes...${NC}"
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true

# Function to start backend
start_backend() {
    echo -e "\n${GREEN}Starting Backend Server (Port 8001)...${NC}"
    cd "$SCRIPT_DIR/admin-backend" || exit 1

    # Install dependencies if needed
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv venv
    fi

    source venv/bin/activate

    # Check and install dependencies
    if ! pip show uvicorn > /dev/null 2>&1; then
        echo -e "${YELLOW}Installing backend dependencies...${NC}"
        pip install -r requirements.txt
    fi

    python run.py &
    BACKEND_PID=$!
    echo $BACKEND_PID > /tmp/yang_rag_backend.pid
    echo -e "${GREEN}Backend started with PID: $BACKEND_PID${NC}"
}

# Function to start frontend
start_frontend() {
    echo -e "\n${GREEN}Starting Frontend (Port 5173)...${NC}"
    cd "$SCRIPT_DIR/admin-frontend" || exit 1

    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing frontend dependencies...${NC}"
        npm install
    fi

    npm run dev &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > /tmp/yang_rag_frontend.pid
    echo -e "${GREEN}Frontend started with PID: $FRONTEND_PID${NC}"
}

# Start services
start_backend
start_frontend

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Services Started Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n${YELLOW}Frontend:${NC} http://localhost:5173"
echo -e "${YELLOW}Backend API:${NC} http://localhost:8001"
echo -e "${YELLOW}API Docs:${NC} http://localhost:8001/docs"
echo -e "\n${YELLOW}Default Credentials:${NC}"
echo -e "  Username: admin"
echo -e "  Password: admin123"
echo -e "\n${GREEN}========================================${NC}"
echo -e "Press Ctrl+C to stop all services"
echo -e "${GREEN}========================================${NC}"

# Wait for any process to exit
wait
