#!/bin/bash

# Magic Card Scanner - Development Database Setup
# This script copies the production database to create a development database

echo "🛠️ Setting up Development Database..."

# Change to project directory
cd "$(dirname "$0")"

# Check if production database exists
if [ ! -f "magic_cards.db" ]; then
    echo "❌ Production database (magic_cards.db) not found!"
    echo "Please ensure the production database exists first."
    exit 1
fi

# Create development database by copying production
echo "📋 Copying production database to development..."
cp magic_cards.db magic_cards_dev.db

# Check if copy was successful
if [ -f "magic_cards_dev.db" ]; then
    echo "✅ Development database created successfully!"
    echo "📊 Database file: magic_cards_dev.db"
    
    # Show database size
    DEV_SIZE=$(ls -lh magic_cards_dev.db | awk '{print $5}')
    echo "📏 Database size: $DEV_SIZE"
    
    # Show record count
    RECORD_COUNT=$(sqlite3 magic_cards_dev.db "SELECT COUNT(*) FROM cards WHERE deleted = 0;")
    echo "📝 Active cards: $RECORD_COUNT"
    
    echo ""
    echo "🚀 You can now start the development server:"
    echo "   ./start_server_dev.sh"
    echo ""
    echo "🌐 Development server will run on: http://localhost:8001"
    echo "🌐 Production server runs on: http://localhost:8000"
else
    echo "❌ Failed to create development database!"
    exit 1
fi 