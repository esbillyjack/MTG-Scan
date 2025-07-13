#!/bin/bash

# Magic Card Scanner - Enhanced Server Startup Script with Auto Backup
# This script runs both the server and auto backup daemon as background services

echo "🚀 Starting Magic Card Scanner Server with Auto Backup..."

# Change to project directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Create logs and backups directories if they don't exist
mkdir -p logs
mkdir -p backups

# Check if server is already running
if [ -f "logs/server.pid" ]; then
    SERVER_PID=$(cat logs/server.pid)
    if ps -p $SERVER_PID > /dev/null 2>&1; then
        echo "⚠️  Server is already running with PID: $SERVER_PID"
        echo "   Use ./stop_server.sh to stop it first"
        exit 1
    else
        # Remove stale PID file
        rm logs/server.pid
    fi
fi

# Check if auto backup is already running
if [ -f "logs/backup.pid" ]; then
    BACKUP_PID=$(cat logs/backup.pid)
    if ps -p $BACKUP_PID > /dev/null 2>&1; then
        echo "⚠️  Auto backup daemon is already running with PID: $BACKUP_PID"
        echo "   Use ./stop_backup.sh to stop it first"
        exit 1
    else
        # Remove stale PID file
        rm logs/backup.pid
    fi
fi

# Start auto backup daemon first
echo "💾 Starting auto backup daemon..."
nohup venv/bin/python auto_backup.py --daemon --interval 6 > logs/backup.log 2>&1 &
BACKUP_PID=$!
echo $BACKUP_PID > logs/backup.pid
echo "✅ Auto backup daemon started with PID: $BACKUP_PID"

# Start server
echo "🌐 Starting web server..."
nohup venv/bin/python backend/app.py > logs/server.log 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > logs/server.pid
echo "✅ Server started with PID: $SERVER_PID"

# Create an initial backup
echo "📦 Creating initial backup..."
venv/bin/python backup_manager.py backup --name "startup_backup_$(date +%Y%m%d_%H%M%S)" > /dev/null 2>&1

echo ""
echo "🎉 Magic Card Scanner is now running!"
echo "📝 Server logs: logs/server.log"
echo "💾 Backup logs: logs/backup.log"
echo "🌐 Access: http://localhost:8000"
echo "⏰ Auto backup: Every 6 hours"
echo ""
echo "Management commands:"
echo "  ./stop_server.sh         - Stop both server and backup daemon"
echo "  ./check_server.sh        - Check status of all services"
echo "  ./backup_manager.py list - View all backups"
echo ""
echo "Press Ctrl+C to stop (or use ./stop_server.sh)" 