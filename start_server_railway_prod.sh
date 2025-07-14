#!/bin/bash

# Magic Card Scanner - Railway Production Server (using dev database with real data)
# This script connects to Railway PostgreSQL development database which has the migrated data

echo "🚀 Starting Magic Card Scanner with Railway Database (Production Mode)..."

# Change to project directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Set environment variables for production mode
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export PORT=8000
export ENV_MODE="production"

# Use Railway development database URL (which has the real migrated data)
export DATABASE_URL="postgresql://postgres:NuhLRXDVKTjRQNPLdSKvPoADLSrnrsjJ@turntable.proxy.rlwy.net:12246/railway"

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the server
echo "📍 Server will be available at: http://localhost:8000"
echo "🌐 Using Railway PostgreSQL database (with migrated data)"
echo "🔗 Database: postgresql://postgres:***@turntable.proxy.rlwy.net:12246/railway"
echo "📊 Collection contains your migrated card data"
echo ""

# Run the server with proper error handling
python backend/app.py 2>&1 | tee logs/server_railway_prod.log 