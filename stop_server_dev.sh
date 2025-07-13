#!/bin/bash

# Magic Card Scanner - Development Server Stop Script

echo "🛑 Stopping Magic Card Scanner Development Server..."

# Change to project directory
cd "$(dirname "$0")"

# Check if PID file exists
if [ -f "logs/server_dev.pid" ]; then
    PID=$(cat logs/server_dev.pid)
    
    # Check if process is still running
    if ps -p $PID > /dev/null 2>&1; then
        echo "Found development server running with PID: $PID"
        
        # Try graceful shutdown first
        kill $PID
        
        # Wait a bit and check if it's still running
        sleep 2
        if ps -p $PID > /dev/null 2>&1; then
            echo "Process still running, forcing shutdown..."
            kill -9 $PID
        fi
        
        echo "✅ Development server stopped"
    else
        echo "⚠️ Development server process not found (PID: $PID)"
    fi
    
    # Clean up PID file
    rm -f logs/server_dev.pid
else
    echo "ℹ️ No development server PID file found"
fi

echo "🔍 Development server status: Stopped" 