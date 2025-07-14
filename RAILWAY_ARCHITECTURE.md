# Railway Architecture - Two Environment Setup

## **Current Architecture (Two Railway Projects)**

### **🔧 Railway Development** 
- **Project**: `astonishing-hope`
- **Branch**: `develop` 
- **URL**: https://mtg-scan-production.up.railway.app/
- **Database**: PostgreSQL (with 79 cards migrated)
- **Purpose**: Testing new features, development work

### **🚀 Railway Production** 
- **Project**: `astonishing-hope` 
- **Branch**: `production`
- **URL**: https://mtg-scan-production.up.railway.app/
- **Database**: PostgreSQL (with 79 cards + complete scan history migrated)
- **Purpose**: Stable production deployment

### **🏠 Local Development**
- **Branch**: `develop`
- **Port**: 8001
- **Database**: SQLite (`magic_cards_dev.db`)
- **Purpose**: Local development and testing

### **🏠 Local Production**
- **Branch**: `production` 
- **Port**: 8000
- **Database**: SQLite (`magic_cards.db`)
- **Purpose**: Local production testing

## **Development → Production Workflow**

### **Step 1: Develop Features**
```bash
# Work on develop branch locally
git checkout develop
./start_server_dev.sh  # localhost:8001
```

### **Step 2: Test on Railway Development**
```bash
# Push to develop branch
git push origin develop
# Auto-deploys to https://mtg-scan-production.up.railway.app/
```

### **Step 3: Merge to Production**
```bash
# When ready for production
git checkout production
git merge develop
git push origin production
# Auto-deploys to Railway Production URL
```

### **Step 4: Migrate Data (if needed)**
```bash
# Use migration scripts to sync data between environments
python migrate_to_railway_api.py  # For data migration
```

## **Environment Variables**

### **Development (astonishing-hope)**
- `ENV_MODE=production` (misleading name, but this is dev)
- `PORT=8000`
- `OPENAI_API_KEY=sk-proj-...`
- `JWT_SECRET_KEY=railway-production-secret-2025`

### **Production (MTG Scan)**
- `ENV_MODE=production`
- `PORT=8000`
- `OPENAI_API_KEY=sk-proj-...` (same key)
- `JWT_SECRET_KEY=railway-production-secret-2025`

## **Database Strategy**

### **Development Databases**
- **Local**: SQLite (`magic_cards_dev.db`)
- **Railway**: PostgreSQL (has test data)

### **Production Databases**
- **Local**: SQLite (`magic_cards.db` - your main collection)
- **Railway**: PostgreSQL (empty, ready for production)

## **Branch Management**

### **develop branch**
- Active development
- Experimental features
- Auto-deploys to Railway Development

### **production branch**
- Stable releases only
- Thoroughly tested features
- Auto-deploys to Railway Production

## **Benefits of This Architecture**

1. **🔒 Safe Development**: Test features without affecting production
2. **🚀 Easy Deployment**: Push to branch = automatic deployment
3. **🗄️ Database Isolation**: Separate databases for each environment
4. **📊 Testing Pipeline**: develop → production promotion workflow
5. **🔧 Local Control**: Full local development capabilities

## **Next Steps**

1. **Complete Railway Production Setup** (in progress)
2. **Migrate Production Data** to Railway Production
3. **Set Up CI/CD** for automated testing
4. **Phase 2: Authentication** when ready 