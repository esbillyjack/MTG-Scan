#!/usr/bin/env python3
"""
Migrate scan images from local production to Railway with persistent volumes.
Run this AFTER enabling Railway Volumes and deploying updated code.
"""

import requests
import sqlite3
import os
from pathlib import Path
import time

# Railway configuration
RAILWAY_URL = "https://mtg-scan-production.up.railway.app"  # Update with your Railway URL

def check_railway_volumes():
    """Check if Railway volumes are working"""
    try:
        response = requests.get(f"{RAILWAY_URL}/api/environment", timeout=10)
        if response.status_code == 200:
            print("✅ Railway API is accessible")
            return True
        else:
            print(f"❌ Railway API returned HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Railway: {e}")
        return False

def get_scan_images_with_cards():
    """Get all scan images that have associated cards"""
    print("📦 Reading scan images from local production database...")
    
    try:
        conn = sqlite3.connect("magic_cards.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get scan images that have cards (cleaned up database)
        cursor.execute("""
            SELECT DISTINCT si.filename, si.scan_id, s.created_at
            FROM scan_images si
            JOIN scans s ON si.scan_id = s.id
            JOIN cards c ON s.id = c.scan_id AND c.deleted = 0
            ORDER BY si.scan_id DESC
        """)
        
        images = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        print(f"📊 Found {len(images)} scan images with associated cards")
        return images
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return []

def upload_scan_image(filename, scan_id):
    """Upload a single scan image to Railway"""
    local_path = f"uploads/{filename}"
    
    if not os.path.exists(local_path):
        print(f"⚠️  File not found: {local_path}")
        return False
    
    try:
        with open(local_path, 'rb') as f:
            files = {'file': (filename, f, 'image/jpeg')}
            data = {'scan_id': scan_id}
            
            response = requests.post(
                f"{RAILWAY_URL}/upload",  # Using existing upload endpoint
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code == 200:
            print(f"✅ Uploaded {filename} (scan {scan_id})")
            return True
        else:
            print(f"❌ Failed {filename}: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Upload error for {filename}: {e}")
        return False

def migrate_all_images():
    """Main migration function"""
    print("🚀 Railway Scan Image Migration")
    print("=" * 50)
    
    # Pre-flight checks
    if not check_railway_volumes():
        print("❌ Railway not accessible. Check your Railway URL and deployment.")
        return False
    
    # Get images to migrate
    images = get_scan_images_with_cards()
    if not images:
        print("❌ No images found to migrate")
        return False
    
    # Confirm migration
    # print(f"\n📤 Ready to migrate {len(images)} images to Railway volumes")
    # print(f"🎯 Target: {RAILWAY_URL}")
    
    # confirm = input("\nProceed with migration? (y/N): ").lower().strip()
    # if confirm != 'y':
    #     print("❌ Migration cancelled")
    #     return False
    
    # Migrate images
    successful = 0
    failed = 0
    
    print(f"\n🔄 Starting migration...")
    
    for i, image in enumerate(images, 1):
        print(f"[{i}/{len(images)}] ", end="")
        
        if upload_scan_image(image['filename'], image['scan_id']):
            successful += 1
        else:
            failed += 1
        
        # Small delay to avoid overwhelming the server
        time.sleep(0.5)
    
    # Summary
    print(f"\n📊 Migration Complete!")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📁 Total: {len(images)}")
    
    if failed == 0:
        print("\n🎉 All images successfully migrated to Railway volumes!")
        print("🔗 Check scan history at:", f"{RAILWAY_URL}")
    else:
        print(f"\n⚠️  {failed} images failed to upload. Check Railway logs for details.")
    
    return failed == 0

if __name__ == "__main__":
    try:
        migrate_all_images()
    except KeyboardInterrupt:
        print("\n❌ Migration interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}") 