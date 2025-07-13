#!/bin/bash

# Magic Card Scanner - Development Server Status Check
# This script checks the status of the development server on port 8001

echo "🔍 Checking Magic Card Scanner Development Server Status..."

# Change to project directory
cd "$(dirname "$0")"

# Check if PID file exists
if [ -f "logs/server_dev.pid" ]; then
    PID=$(cat logs/server_dev.pid)
    
    # Check if process is running
    if kill -0 $PID 2>/dev/null; then
        echo "✅ Development server is RUNNING (PID: $PID)"
        echo "🌐 Access: http://localhost:8001"
    else
        echo "❌ Development server is NOT RUNNING (stale PID file)"
        rm logs/server_dev.pid
    fi
else
    echo "❌ Development server is NOT RUNNING (no PID file)"
fi

# Check if port 8001 is in use
if lsof -ti:8001 >/dev/null 2>&1; then
    echo "🔌 Port 8001 is active"
    DEV_PROCESSES=$(lsof -ti:8001 2>/dev/null)
    echo "📋 Processes on port 8001: $DEV_PROCESSES"
else
    echo "🔌 Port 8001 is available"
fi

# Show recent development logs if they exist
if [ -f "logs/server_dev.log" ]; then
    echo ""
    echo "📝 Recent development logs (last 5 lines):"
    tail -5 logs/server_dev.log
fi

echo ""
echo "🚀 Production server status: ./check_server.sh" 