#!/bin/bash

# Magic Card Scanner - Development Server Stop Script
# This script stops the development server running on port 8001

echo "🛑 Stopping Magic Card Scanner Development Server..."

# Change to project directory
cd "$(dirname "$0")"

# Check if PID file exists
if [ -f "logs/server_dev.pid" ]; then
    PID=$(cat logs/server_dev.pid)
    
    # Check if process is running
    if kill -0 $PID 2>/dev/null; then
        echo "📋 Found development server with PID: $PID"
        
        # Stop the process
        kill $PID
        
        # Wait for process to stop
        sleep 2
        
        # Check if it's still running
        if kill -0 $PID 2>/dev/null; then
            echo "⚠️  Process still running, force killing..."
            kill -9 $PID
            sleep 1
        fi
        
        # Remove PID file
        rm logs/server_dev.pid
        
        echo "✅ Development server stopped successfully"
    else
        echo "⚠️  Development server not running (PID $PID not found)"
        rm logs/server_dev.pid
    fi
else
    echo "⚠️  No development server PID file found"
fi

# Also check for any processes on port 8001
DEV_PROCESSES=$(lsof -ti:8001 2>/dev/null)
if [ ! -z "$DEV_PROCESSES" ]; then
    echo "🔍 Found processes on port 8001, stopping them..."
    echo $DEV_PROCESSES | xargs kill -9
    echo "✅ Processes on port 8001 stopped"
fi

echo "🏁 Development server shutdown complete" 