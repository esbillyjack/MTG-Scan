#!/bin/bash

# Magic Card Scanner - Server Status Check

echo "🔍 Checking Magic Card Scanner Server Status..."

# Change to project directory
cd "$(dirname "$0")"

# Check if PID file exists
if [ -f "logs/server.pid" ]; then
    SERVER_PID=$(cat logs/server.pid)
    
    # Check if process is running
    if ps -p $SERVER_PID > /dev/null 2>&1; then
        echo "✅ Server is RUNNING (PID: $SERVER_PID)"
        echo "🌐 Access: http://localhost:8000"
        
        # Check if port is listening
        if lsof -i :8000 > /dev/null 2>&1; then
            echo "🔌 Port 8000 is active"
        else
            echo "⚠️  Port 8000 is not responding"
        fi
        
        # Show recent logs
        if [ -f "logs/server.log" ]; then
            echo ""
            echo "📝 Recent logs:"
            tail -5 logs/server.log
        fi
    else
        echo "❌ Server is NOT RUNNING (PID: $SERVER_PID not found)"
        echo "💡 Start server with: ./start_server.sh"
    fi
else
    echo "❌ No server PID file found"
    echo "💡 Start server with: ./start_server.sh"
fi

# Check for any other server processes
echo ""
echo "🔍 Checking for other server processes..."
ps aux | grep "python backend/app.py" | grep -v grep 