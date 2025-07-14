#!/bin/bash

# Magic Card Scanner - Stop Production Server Script

echo "🛑 Stopping Magic Card Scanner Production Server..."

# Find and kill the production server process
PID=$(ps aux | grep "python backend/app.py" | grep -v grep | awk '{print $2}')

if [ -n "$PID" ]; then
    echo "🔍 Found server process: $PID"
    kill $PID
    echo "✅ Server stopped successfully"
else
    echo "⚠️ No server process found"
fi

# Also check for any uvicorn processes on port 8000
UVICORN_PID=$(lsof -ti:8000 2>/dev/null)
if [ -n "$UVICORN_PID" ]; then
    echo "🔍 Found process on port 8000: $UVICORN_PID"
    kill $UVICORN_PID
    echo "✅ Port 8000 freed"
fi

echo "🏁 Production server shutdown complete" 