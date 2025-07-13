#!/bin/bash

# Magic Card Scanner - Production Server Startup Script
# This script runs the production server from the production directory

echo "🚀 Starting Magic Card Scanner Production Server..."

# Change to project directory (we're already in production directory)
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Set environment variables for production
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export PORT=8000
export ENV_MODE="production"

# Create logs directory if it doesn't exist
mkdir -p logs

# Start server with nohup to persist through sleep/lock
nohup venv/bin/python backend/app.py > logs/server.log 2>&1 &

# Get the process ID
SERVER_PID=$!

# Save PID to file for easy management
echo $SERVER_PID > logs/server.pid

echo "✅ Production server started with PID: $SERVER_PID"
echo "📝 Logs: logs/server.log"
echo "🌐 Access: http://localhost:8000"
echo ""
echo "To stop the server: ./stop_server.sh"
echo "To check status: ./check_server.sh"
echo ""
echo "🛠️ Development server (port 8001): ./start_server_dev.sh" 