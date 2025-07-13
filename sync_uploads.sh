#!/bin/bash

# Sync Uploads Script
# Copies new uploaded files from development to production

echo "🔄 Syncing uploads from development to production..."

DEV_UPLOADS="uploads/"
PROD_UPLOADS="../magic-card-scanner-production/uploads/"

# Check if directories exist
if [ ! -d "$DEV_UPLOADS" ]; then
    echo "❌ Development uploads directory not found"
    exit 1
fi

if [ ! -d "$PROD_UPLOADS" ]; then
    echo "❌ Production uploads directory not found"
    exit 1
fi

# Count files before sync
DEV_COUNT=$(ls "$DEV_UPLOADS" | grep -v ".gitkeep" | wc -l)
PROD_COUNT=$(ls "$PROD_UPLOADS" | grep -v ".gitkeep" | wc -l)

echo "📊 Before sync:"
echo "   Development: $DEV_COUNT files"
echo "   Production: $PROD_COUNT files"

# Copy files (will overwrite if newer)
echo "📁 Copying files..."
rsync -av --exclude=".gitkeep" "$DEV_UPLOADS" "$PROD_UPLOADS"

# Count files after sync
NEW_PROD_COUNT=$(ls "$PROD_UPLOADS" | grep -v ".gitkeep" | wc -l)

echo "📊 After sync:"
echo "   Production: $NEW_PROD_COUNT files"

if [ "$NEW_PROD_COUNT" -eq "$DEV_COUNT" ]; then
    echo "✅ Upload sync completed successfully"
else
    echo "⚠️ Sync completed but file counts don't match"
fi

echo ""
echo "💡 To test image serving:"
echo "   Development: http://localhost:8001/uploads/"
echo "   Production:  http://localhost:8000/uploads/" 