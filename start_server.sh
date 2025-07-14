#!/bin/bash

# Magic Card Scanner - Production Server Startup Script
# This script runs the production server on port 8000

echo "🚀 Starting Magic Card Scanner Production Server..."

# Change to project directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Set environment variables for production
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export PORT=8000
export ENV_MODE="production"

# Ensure DATABASE_URL is not set to use local SQLite logic
unset DATABASE_URL

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the server
echo "📍 Server will be available at: http://localhost:8000"
echo "🗄️ Using local SQLite database: magic_cards.db"
echo "📊 Collection contains $(sqlite3 magic_cards.db 'SELECT COUNT(*) FROM cards WHERE deleted = 0;' 2>/dev/null || echo '0') cards"
echo ""

# Run the server with proper error handling
python backend/app.py 2>&1 | tee logs/server.log 