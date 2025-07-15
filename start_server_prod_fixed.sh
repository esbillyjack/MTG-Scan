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

# Use production PostgreSQL database
export DATABASE_URL="postgresql://postgres:BicHTleuATnAIkRFBcqTDXMwwyuIXEAA@turntable.proxy.rlwy.net:35800/railway"

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the server
echo "📍 Server will be available at: http://localhost:8000"
echo "🌐 Using production PostgreSQL database"
echo "🔗 Database: postgresql://postgres:***@turntable.proxy.rlwy.net:35800/railway"
echo "📊 Loading production data with scan history..."
echo ""

# Run the server with proper error handling
python backend/app.py 2>&1 | tee logs/server.log 