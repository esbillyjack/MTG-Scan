#!/bin/bash

# Magic Card Scanner - Quick Backup Status

echo "📦 Magic Card Scanner Backup Status"
echo "=================================="

# Change to project directory
cd "$(dirname "$0")"

# Check if backup daemon is running
if [ -f "logs/backup.pid" ]; then
    BACKUP_PID=$(cat logs/backup.pid)
    if ps -p $BACKUP_PID > /dev/null 2>&1; then
        echo "✅ Auto backup daemon: RUNNING (PID: $BACKUP_PID)"
    else
        echo "❌ Auto backup daemon: NOT RUNNING"
    fi
else
    echo "❌ Auto backup daemon: NOT RUNNING (no PID file)"
fi

# Show backup statistics
echo ""
echo "📊 Database Stats:"
if command -v python &> /dev/null && [ -f "backup_manager.py" ]; then
    python backup_manager.py stats 2>/dev/null | grep -E "(total_cards|database_size|last_backup)" | sed 's/^/  /'
else
    echo "  Stats unavailable"
fi

# Show backup directory info
echo ""
echo "💾 Available Backups:"
if [ -d "backups" ]; then
    BACKUP_COUNT=$(ls -1 backups/*.zip 2>/dev/null | wc -l)
    if [ $BACKUP_COUNT -gt 0 ]; then
        echo "  Found: $BACKUP_COUNT backup file(s)"
        
        # Show latest 3 backups
        echo "  Latest backups:"
        ls -t backups/*.zip 2>/dev/null | head -3 | while read backup; do
            SIZE=$(du -h "$backup" | cut -f1)
            DATE=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$backup" 2>/dev/null || date -r "$backup" "+%Y-%m-%d %H:%M" 2>/dev/null || echo "Unknown")
            echo "    $(basename "$backup") ($SIZE) - $DATE"
        done
        
        if [ $BACKUP_COUNT -gt 3 ]; then
            echo "    ... and $((BACKUP_COUNT - 3)) more"
        fi
    else
        echo "  No backup files found"
    fi
else
    echo "  Backups directory not found"
fi

echo ""
echo "🔧 Quick Actions:"
echo "  Create backup:     python backup_manager.py backup"
echo "  List all backups:  python backup_manager.py list"
echo "  Export data:       python backup_manager.py export"
echo "  Check full status: ./check_server.sh" 