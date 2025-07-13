#!/bin/bash

# Magic Card Scanner - Server Startup Script
# This script runs the server as a background service that persists through sleep/lock

echo "🚀 Starting Magic Card Scanner Server..."

# Change to project directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Create logs directory if it doesn't exist
mkdir -p logs

# Start server with nohup to persist through sleep/lock
nohup venv/bin/python backend/app.py > logs/server.log 2>&1 &

# Get the process ID
SERVER_PID=$!

# Save PID to file for easy management
echo $SERVER_PID > logs/server.pid

echo "✅ Server started with PID: $SERVER_PID"
echo "📝 Logs: logs/server.log"
echo "🌐 Access: http://localhost:8000"
echo ""
echo "To stop the server: ./stop_server.sh"
echo "To check status: ./check_server.sh" 