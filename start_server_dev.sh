#!/bin/bash

# Magic Card Scanner - Development Server Startup Script
# This script runs the development server on port 8001

echo "🛠️ Starting Magic Card Scanner Development Server..."

# Change to project directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Load environment variables from .env file
if [ -f .env ]; then
    echo "📄 Loading environment variables from .env file..."
    source .env
fi

# Set environment variables for development
export PORT=8001
export ENV_MODE="development"

# Create logs directory if it doesn't exist
mkdir -p logs

# Start development server using main.py from root directory
echo "🚀 Starting server from root directory on port 8001..."
nohup env ENV_MODE=development PORT=8001 DATABASE_URL_DEV="$DATABASE_URL_DEV" venv/bin/python main.py > logs/server_dev.log 2>&1 &

# Get the process ID
SERVER_PID=$!

# Save PID to file for easy management
echo $SERVER_PID > logs/server_dev.pid

echo "✅ Development server started with PID: $SERVER_PID"
echo "📝 Logs: logs/server_dev.log"
echo "🌐 Access: http://localhost:8001"
echo ""
echo "To stop the dev server: ./stop_server_dev.sh"
echo "To check dev status: ./check_server_dev.sh"
echo ""
echo "🚀 Production server (port 8000): ./start_server.sh" 