#!/bin/bash

# Magic Card Scanner - Railway Development Database Server
# This script connects to Railway PostgreSQL development database

echo "🚀 Starting Magic Card Scanner with Railway Development Database..."

# Change to project directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Set environment variables for Railway development
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export PORT=8001
export ENV_MODE="development"

# Set Railway PostgreSQL development database URL
export DATABASE_URL="postgresql://postgres:NuhLRXDVKTjRQNPLdSKvPoADLSrnrsjJ@turntable.proxy.rlwy.net:12246/railway"

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the server
echo "📍 Server will be available at: http://localhost:8001"
echo "🌐 Using Railway PostgreSQL development database"
echo "🔗 Database: postgresql://postgres:***@turntable.proxy.rlwy.net:12246/railway"
echo ""

# Run the server with proper error handling
python backend/app.py 2>&1 | tee logs/server_railway_dev.log 