#!/bin/bash

# Magic Card Scanner Server Status Checker
# Checks the status of both development and production servers

echo "🔍 Magic Card Scanner Server Status"
echo "=================================="

PRODUCTION_DIR="../magic-card-scanner-production"
CURRENT_DIR="$(pwd)"

# Function to check server status
check_server_status() {
    local server_name="$1"
    local pid_file="$2"
    local port="$3"
    local log_file="$4"
    
    echo ""
    echo "📊 $server_name Server Status:"
    echo "--------------------------------"
    
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if ps -p $PID > /dev/null 2>&1; then
            echo "✅ Status: Running (PID: $PID)"
            echo "🌐 URL: http://localhost:$port"
            
            # Check if the server is responding
            if curl -s "http://localhost:$port/api/health" > /dev/null 2>&1; then
                echo "🔌 Health Check: Responding"
            else
                echo "❌ Health Check: Not responding"
            fi
            
            # Show recent log entries
            if [ -f "$log_file" ]; then
                echo "📝 Recent logs:"
                tail -n 3 "$log_file" | sed 's/^/    /'
            else
                echo "⚠️ No log file found"
            fi
        else
            echo "❌ Status: Not running (stale PID file)"
            rm -f "$pid_file"
        fi
    else
        echo "⭕ Status: Not running"
    fi
}

# Check development server
check_server_status "Development" "$CURRENT_DIR/logs/server_dev.pid" "8001" "$CURRENT_DIR/logs/server_dev.log"

# Check production server
check_server_status "Production" "$PRODUCTION_DIR/logs/server.pid" "8000" "$PRODUCTION_DIR/logs/server.log"

echo ""
echo "💡 Quick Actions:"
echo "- Start development server: ./start_server_dev.sh"
echo "- Start production server: ./start_server.sh"
echo "- Stop development server: ./stop_server_dev.sh"
echo "- Stop production server: ./stop_server.sh"
echo "- Deploy to production: ./deploy.sh"
echo "- View development logs: tail -f logs/server_dev.log"
echo "- View production logs: tail -f $PRODUCTION_DIR/logs/server.log" 