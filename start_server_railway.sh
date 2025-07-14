#!/bin/bash

# Magic Card Scanner - Railway Production Database Server
# This script connects to Railway PostgreSQL production database

echo "🚀 Starting Magic Card Scanner with Railway Production Database..."

# Change to project directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Set environment variables for Railway production
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export PORT=8000
export ENV_MODE="production"

# Set Railway PostgreSQL production database URL
export DATABASE_URL="postgresql://postgres:BicHTleuATnAIkRFBcqTDXMwwyuIXEAA@turntable.proxy.rlwy.net:35800/railway"

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the server
echo "📍 Server will be available at: http://localhost:8000"
echo "🌐 Using Railway PostgreSQL production database"
echo "🔗 Database: postgresql://postgres:***@turntable.proxy.rlwy.net:35800/railway"
echo ""

# Run the server with proper error handling
python backend/app.py 2>&1 | tee logs/server_railway.log 