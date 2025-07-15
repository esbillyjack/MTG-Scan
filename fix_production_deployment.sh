#!/bin/bash

# Fix Production Deployment Script
# This script properly resets production and forces deployment

set -e

echo "🔧 Fixing production deployment..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
PROD_DB_URL="postgresql://postgres:BicHTleuATnAIkRFBcqTDXMwwyuIXEAA@turntable.proxy.rlwy.net:35800/railway"
DEV_DB_URL="postgresql://postgres:NuhLRXDVKTjRQNPLdSKvPoADLSrnrsjJ@turntable.proxy.rlwy.net:12246/railway"

echo -e "${YELLOW}Step 1: Creating fresh backup of development database...${NC}"
BACKUP_FILE="dev_backup_$(date +%Y%m%d_%H%M%S).sql"
pg_dump "$DEV_DB_URL" > "$BACKUP_FILE"
echo "✅ Backup created: $BACKUP_FILE"

echo -e "${YELLOW}Step 2: Completely wiping production database...${NC}"
psql "$PROD_DB_URL" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
echo "✅ Production database wiped"

echo -e "${YELLOW}Step 3: Importing clean development data...${NC}"
psql "$PROD_DB_URL" < "$BACKUP_FILE"
echo "✅ Development data imported to production"

echo -e "${YELLOW}Step 4: Force Railway deployment...${NC}"
echo "🚀 Pushing latest code to main branch..."
git push origin main --force

echo -e "${YELLOW}Step 5: Checking Railway deployment status...${NC}"
echo "📋 Please check Railway dashboard for deployment status"
echo "🌐 Production URL: https://mtg-scan-production.up.railway.app"

echo ""
echo -e "${GREEN}✅ Production deployment fix completed!${NC}"
echo ""
echo "Next steps:"
echo "1. Check Railway dashboard for deployment status"
echo "2. Wait for deployment to complete (usually 2-5 minutes)"
echo "3. Test production app: https://mtg-scan-production.up.railway.app"
echo "4. Verify scan images are working" 