#!/bin/bash

# Magic Card Scanner - Server and Backup Status Check

echo "🔍 Checking Magic Card Scanner Services Status..."

# Change to project directory
cd "$(dirname "$0")"

# Check server status
echo "🌐 SERVER STATUS:"
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
    else
        echo "❌ Server is NOT RUNNING (PID: $SERVER_PID not found)"
        echo "💡 Start with: ./start_server.sh or ./start_server_with_backup.sh"
    fi
else
    echo "❌ No server PID file found"
    echo "💡 Start with: ./start_server.sh or ./start_server_with_backup.sh"
fi

# Check backup daemon status
echo ""
echo "💾 BACKUP DAEMON STATUS:"
if [ -f "logs/backup.pid" ]; then
    BACKUP_PID=$(cat logs/backup.pid)
    
    # Check if process is running
    if ps -p $BACKUP_PID > /dev/null 2>&1; then
        echo "✅ Backup daemon is RUNNING (PID: $BACKUP_PID)"
        echo "⏰ Auto backup every 6 hours"
        
        # Show backup stats
        if command -v python &> /dev/null; then
            echo "📊 Latest backup info:"
            python backup_manager.py stats 2>/dev/null | grep -E "(total_cards|last_backup)" || echo "   Stats unavailable"
        fi
    else
        echo "❌ Backup daemon is NOT RUNNING (PID: $BACKUP_PID not found)"
        echo "💡 Start with: ./start_server_with_backup.sh"
    fi
else
    echo "❌ No backup daemon PID file found"
    echo "💡 Start with: ./start_server_with_backup.sh"
fi

# Show recent logs
echo ""
echo "📝 RECENT LOGS:"
if [ -f "logs/server.log" ]; then
    echo "Server logs (last 3 lines):"
    tail -3 logs/server.log | sed 's/^/  /'
fi

if [ -f "logs/backup.log" ]; then
    echo "Backup logs (last 3 lines):"
    tail -3 logs/backup.log | sed 's/^/  /'
fi

# Check for any other processes
echo ""
echo "🔍 OTHER PROCESSES:"
SERVER_PROCS=$(ps aux | grep "python backend/app.py" | grep -v grep | wc -l)
BACKUP_PROCS=$(ps aux | grep "auto_backup.py" | grep -v grep | wc -l)

if [ $SERVER_PROCS -gt 0 ]; then
    echo "Found $SERVER_PROCS server process(es)"
fi

if [ $BACKUP_PROCS -gt 0 ]; then
    echo "Found $BACKUP_PROCS backup process(es)"
fi

# Show backup directory info
echo ""
echo "📦 BACKUP SUMMARY:"
if [ -d "backups" ]; then
    BACKUP_COUNT=$(ls -1 backups/*.zip 2>/dev/null | wc -l)
    if [ $BACKUP_COUNT -gt 0 ]; then
        echo "Found $BACKUP_COUNT backup file(s)"
        echo "Latest backup: $(ls -t backups/*.zip 2>/dev/null | head -1 | xargs basename)"
        echo "Use 'python backup_manager.py list' for details"
    else
        echo "No backup files found"
    fi
else
    echo "Backups directory not found"
fi 