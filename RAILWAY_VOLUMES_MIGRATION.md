# Railway Volumes Implementation & Scan Data Migration

## 🎯 **Objective**: Transition from SQLite to Railway PostgreSQL with persistent file storage

### **Current Architecture Issues**
1. **Ephemeral Storage**: Railway's default file system loses scan images on deployment
2. **Database Mismatch**: Local SQLite ≠ Railway PostgreSQL scan data  
3. **Missing Scan Images**: No persistent storage for user-uploaded scan files

---

## 🛠️ **Solution: Railway Volumes Implementation**

### **Step 1: Enable Railway Volumes**

1. **Go to Railway Dashboard** → Your Project
2. **Select your service** → Settings → Volumes
3. **Add Volume**:
   - **Mount Path**: `/app/uploads`
   - **Size**: 5GB (start with this, can increase later)
   - **Name**: `scan-storage`

### **Step 2: Update Application Configuration**

```python
# backend/app.py - Update uploads directory handling
import os

def get_uploads_path():
    """Get uploads directory path - Railway Volume or local"""
    if os.getenv("RAILWAY_ENVIRONMENT"):
        # Railway deployment - use mounted volume
        uploads_path = "/app/uploads"
    else:
        # Local development - use relative path
        uploads_path = "uploads"
    
    # Ensure directory exists
    os.makedirs(uploads_path, exist_ok=True)
    return uploads_path

# Update all file operations to use get_uploads_path()
UPLOADS_DIR = get_uploads_path()

# Update FastAPI static mount
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
```

### **Step 3: Environment Detection**

```python
# backend/database.py - Enhanced environment detection
def get_database_config():
    """Determine database configuration based on environment"""
    
    # Priority 1: Railway PostgreSQL (DATABASE_URL exists)
    railway_db_url = os.getenv("DATABASE_URL")
    if railway_db_url:
        print("🚀 Using Railway PostgreSQL")
        return railway_db_url, "postgresql"
    
    # Priority 2: Local Development/Fallback SQLite
    env_mode = os.getenv("ENV_MODE", "production")
    if env_mode == "development":
        sqlite_path = "sqlite:///./magic_cards_dev.db"
    else:
        sqlite_path = "sqlite:///./magic_cards.db"
    
    print(f"🗄️ Using SQLite fallback: {sqlite_path}")
    return sqlite_path, "sqlite"

DATABASE_URL, DB_TYPE = get_database_config()
```

---

## 📊 **Data Migration Strategy**

### **Phase 1: Scan Images Migration**

```python
# migrate_scans_to_railway.py
#!/usr/bin/env python3
"""
Migrate scan images from local SQLite to Railway PostgreSQL + Volumes
"""

import requests
import sqlite3
import os
from pathlib import Path
import json

def migrate_scan_images():
    """Upload all local scan images to Railway"""
    
    # Connect to local database
    conn = sqlite3.connect("magic_cards.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all scan images that have valid cards
    cursor.execute("""
        SELECT DISTINCT si.filename, si.scan_id 
        FROM scan_images si
        JOIN scans s ON si.scan_id = s.id
        JOIN cards c ON s.id = c.scan_id AND c.deleted = 0
        ORDER BY si.scan_id
    """)
    
    images = cursor.fetchall()
    railway_url = "https://mtg-scan-production.up.railway.app"
    
    print(f"📤 Migrating {len(images)} scan images to Railway...")
    
    for image in images:
        local_path = f"uploads/{image['filename']}"
        if os.path.exists(local_path):
            # Upload to Railway
            with open(local_path, 'rb') as f:
                files = {'file': (image['filename'], f, 'image/jpeg')}
                response = requests.post(
                    f"{railway_url}/migrate/scan-image", 
                    files=files,
                    data={'scan_id': image['scan_id']}
                )
            
            if response.status_code == 200:
                print(f"✅ Uploaded {image['filename']}")
            else:
                print(f"❌ Failed {image['filename']}: {response.status_code}")

if __name__ == "__main__":
    migrate_scan_images()
```

### **Phase 2: Database Sync**

```python
# sync_railway_database.py
#!/usr/bin/env python3
"""
Sync Railway PostgreSQL with local SQLite production data
"""

import sqlite3
import psycopg2
import os
from datetime import datetime

def sync_databases():
    """Sync local SQLite data to Railway PostgreSQL"""
    
    # Local SQLite connection
    sqlite_conn = sqlite3.connect("magic_cards.db")
    sqlite_conn.row_factory = sqlite3.Row
    
    # Railway PostgreSQL connection
    railway_db_url = os.getenv("RAILWAY_DATABASE_URL")
    pg_conn = psycopg2.connect(railway_db_url)
    
    print("🔄 Syncing SQLite → Railway PostgreSQL...")
    
    # Sync cards
    sync_cards(sqlite_conn, pg_conn)
    
    # Sync scans (only those with associated cards)
    sync_scans(sqlite_conn, pg_conn)
    
    # Sync scan images
    sync_scan_images(sqlite_conn, pg_conn)
    
    print("✅ Database sync complete!")

def sync_cards(sqlite_conn, pg_conn):
    """Sync cards table"""
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    # Get all non-deleted cards from SQLite
    sqlite_cursor.execute("SELECT * FROM cards WHERE deleted = 0")
    cards = sqlite_cursor.fetchall()
    
    for card in cards:
        # Insert or update in PostgreSQL
        pg_cursor.execute("""
            INSERT INTO cards (unique_id, name, set_code, set_name, ...)
            VALUES (%s, %s, %s, %s, ...)
            ON CONFLICT (unique_id) DO UPDATE SET
            name = EXCLUDED.name,
            set_code = EXCLUDED.set_code,
            ...
        """, tuple(card))
    
    pg_conn.commit()
    print(f"✅ Synced {len(cards)} cards")

# ... similar functions for scans and scan_images
```

---

## 🔧 **Railway Configuration Updates**

### **Update railway.toml**

```toml
# railway.toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python main.py"
healthcheckPath = "/api/environment"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

# Volume configuration
[volumes]
uploads = "/app/uploads"

[environments.production]
ENV_MODE = "production"
PORT = "8000"
RAILWAY_ENVIRONMENT = "production"

[environments.development]
ENV_MODE = "development"  
PORT = "8000"
RAILWAY_ENVIRONMENT = "development"
```

### **Add Migration Endpoint**

```python
# backend/app.py - Add migration endpoint
@app.post("/migrate/scan-image")
async def migrate_scan_image(
    file: UploadFile = File(...), 
    scan_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Endpoint for migrating scan images to Railway volumes"""
    
    # Save to mounted volume
    file_path = f"{UPLOADS_DIR}/{file.filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"status": "success", "filename": file.filename}
```

---

## 📋 **Migration Checklist**

### **Pre-Migration**
- [ ] Railway Volumes enabled and mounted to `/app/uploads`
- [ ] Local SQLite has latest production data
- [ ] Railway PostgreSQL is accessible
- [ ] Migration scripts tested

### **Migration Steps**
1. [ ] **Enable Railway Volumes** (5GB mount to `/app/uploads`)
2. [ ] **Deploy updated code** with volume support
3. [ ] **Run scan image migration** script
4. [ ] **Verify scan images** accessible via Railway
5. [ ] **Sync database records** SQLite → PostgreSQL  
6. [ ] **Test scan history** in Railway environment
7. [ ] **Update local development** to use Railway as fallback

### **Post-Migration**
- [ ] Scan images persist through deployments
- [ ] Scan history shows properly in Railway
- [ ] New scans save to persistent volumes
- [ ] Local SQLite becomes development-only

---

## 🎯 **Best Practices: Railway File Storage**

### **1. Volume vs External Storage**
- **Railway Volumes**: Good for < 50GB, simple setup
- **Cloud Storage** (S3/GCS): Better for > 50GB, CDN integration

### **2. File Organization**
```
/app/uploads/
├── scan_163_uuid.jpg
├── scan_162_uuid.jpg  
└── temp/               # For processing
```

### **3. Backup Strategy**
- Railway Volumes have built-in backups
- Consider periodic export to cloud storage
- Local SQLite becomes emergency fallback

---

## 🚨 **Important Notes**

1. **Zero-Card Policy**: Already implemented in local - will work on Railway
2. **File Persistence**: Volumes persist through deployments (unlike ephemeral)
3. **Cost**: 5GB volume ≈ $2.50/month on Railway Pro plan
4. **Scaling**: Can grow volumes up to 250GB as needed

---

## 🎉 **Expected Outcome**

After migration:
- ✅ **Railway as Official Data Source**: PostgreSQL + persistent file storage
- ✅ **SQLite as Fallback**: Local development + offline mode
- ✅ **Scan History Working**: Images persist and display properly
- ✅ **Zero Downtime**: Users continue using production while dev migrates
- ✅ **Future Ready**: Scalable architecture for growth 