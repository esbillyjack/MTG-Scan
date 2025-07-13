#!/bin/bash

# Magic Card Scanner - Server and Backup Stop Script

echo "🛑 Stopping Magic Card Scanner Server and Auto Backup..."

# Change to project directory
cd "$(dirname "$0")"

# Stop backup daemon first
if [ -f "logs/backup.pid" ]; then
    BACKUP_PID=$(cat logs/backup.pid)
    
    # Check if process is still running
    if ps -p $BACKUP_PID > /dev/null 2>&1; then
        echo "💾 Stopping backup daemon with PID: $BACKUP_PID"
        kill $BACKUP_PID
        
        # Wait a moment and check if it stopped
        sleep 2
        if ps -p $BACKUP_PID > /dev/null 2>&1; then
            echo "⚠️  Backup daemon didn't stop gracefully, force killing..."
            kill -9 $BACKUP_PID
        fi
        
        echo "✅ Backup daemon stopped"
    else
        echo "⚠️  Backup daemon process not found (PID: $BACKUP_PID)"
    fi
    
    # Remove PID file
    rm -f logs/backup.pid
else
    echo "ℹ️  No backup daemon PID file found"
    
    # Try to find and kill any running backup processes
    pkill -f "auto_backup.py --daemon" > /dev/null 2>&1
fi

# Stop server
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

echo "🎉 All services stopped successfully!" 