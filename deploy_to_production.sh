#!/bin/bash

# Magic Card Scanner - Production Deployment Script
# This script safely deploys from development to production

set -e  # Exit on any error

echo "🚀 Starting production deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DEV_DB_URL="postgresql://postgres:NuhLRXDVKTjRQNPLdSKvPoADLSrnrsjJ@turntable.proxy.rlwy.net:12246/railway"
BACKUP_FILE="dev_backup_$(date +%Y%m%d_%H%M%S).sql"

echo -e "${YELLOW}Step 1: Exporting development database...${NC}"
echo "📦 Creating backup: $BACKUP_FILE"

# Export development database
pg_dump "$DEV_DB_URL" > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Development database exported successfully${NC}"
    echo "📊 Backup size: $(du -h "$BACKUP_FILE" | cut -f1)"
else
    echo -e "${RED}❌ Failed to export development database${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 2: Production database setup${NC}"
echo "Please ensure you have:"
echo "1. A production PostgreSQL database created in Railway"
echo "2. The production database URL ready"
echo ""
echo "Options:"
echo "A) Use Railway Dashboard to create/fork database"
echo "B) Provide production database URL for import"
echo ""

# Production database URL (from Railway production environment)
PROD_DB_URL="postgresql://postgres:BicHTleuATnAIkRFBcqTDXMwwyuIXEAA@turntable.proxy.rlwy.net:35800/railway"

echo "🔗 Production database: $PROD_DB_URL"

echo ""
echo -e "${YELLOW}Step 3: Importing to production database...${NC}"

# Clear existing data and import fresh data
echo "🧹 Clearing existing production data..."
psql "$PROD_DB_URL" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

echo "📥 Importing development data..."
psql "$PROD_DB_URL" < "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Data imported to production successfully${NC}"
else
    echo -e "${RED}❌ Failed to import to production database${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 4: Deploying application to production...${NC}"

# Deploy to production
echo "🔄 Pushing to production branch..."
git push origin develop:main

echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo "📊 Backup file: $BACKUP_FILE"
echo "🌐 Production should be available shortly" 