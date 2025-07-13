#!/bin/bash

# Magic Card Scanner - Server Stop Script

echo "🛑 Stopping Magic Card Scanner Server..."

# Change to project directory
cd "$(dirname "$0")"

# Check if PID file exists
if [ -f "logs/server.pid" ]; then
    SERVER_PID=$(cat logs/server.pid)
    
    # Check if process is still running
    if ps -p $SERVER_PID > /dev/null 2>&1; then
        echo "📋 Stopping server with PID: $SERVER_PID"
        kill $SERVER_PID
        
        # Wait a moment and check if it stopped
        sleep 2
        if ps -p $SERVER_PID > /dev/null 2>&1; then
            echo "⚠️  Server didn't stop gracefully, force killing..."
            kill -9 $SERVER_PID
        fi
        
        echo "✅ Server stopped"
    else
        echo "⚠️  Server process not found (PID: $SERVER_PID)"
    fi
    
    # Remove PID file
    rm -f logs/server.pid
else
    echo "⚠️  No server PID file found"
    
    # Try to find and kill any running server processes
    echo "🔍 Looking for running server processes..."
    pkill -f "python backend/app.py"
    echo "✅ Cleaned up server processes"
fi 