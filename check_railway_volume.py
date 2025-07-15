#!/usr/bin/env python3
"""
Check Railway volume contents and scan image accessibility
"""

import os
import sys
import psycopg2
import requests
from pathlib import Path
import json

# Database connection
PROD_DATABASE_URL = "postgresql://postgres:BicHTleuATnAIkRFBcqTDXMwwyuIXEAA@turntable.proxy.rlwy.net:35800/railway"

def check_railway_volume():
    """Check Railway volume contents"""
    print("🔍 RAILWAY VOLUME CHECK")
    print("=" * 40)
    
    # Check if we're running on Railway
    if os.path.exists("/app"):
        print("✅ Running on Railway platform")
        uploads_path = "/app/uploads"
    else:
        print("❌ Not running on Railway platform")
        uploads_path = "uploads"
    
    print(f"📁 Upload path: {uploads_path}")
    
    # Check if uploads directory exists
    if os.path.exists(uploads_path):
        print(f"✅ Uploads directory exists: {uploads_path}")
        
        # List contents
        try:
            files = os.listdir(uploads_path)
            print(f"📊 Found {len(files)} items in uploads directory")
            
            # Show some file details
            image_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif'))]
            print(f"🖼️  Found {len(image_files)} image files")
            
            if image_files:
                print("📋 Sample image files:")
                for i, file in enumerate(image_files[:5]):  # Show first 5
                    file_path = os.path.join(uploads_path, file)
                    try:
                        file_size = os.path.getsize(file_path)
                        print(f"   {i+1}. {file} ({file_size} bytes)")
                    except Exception as e:
                        print(f"   {i+1}. {file} (Error: {e})")
            else:
                print("❌ No image files found in uploads directory")
                
        except Exception as e:
            print(f"❌ Error listing uploads directory: {e}")
            
    else:
        print(f"❌ Uploads directory does not exist: {uploads_path}")
        
        # Try to create it
        try:
            os.makedirs(uploads_path, exist_ok=True)
            print(f"✅ Created uploads directory: {uploads_path}")
        except Exception as e:
            print(f"❌ Failed to create uploads directory: {e}")

def check_database_scan_images():
    """Check what scan images are referenced in the database"""
    print("\n🗄️  DATABASE SCAN IMAGES CHECK")
    print("=" * 40)
    
    try:
        conn = psycopg2.connect(PROD_DATABASE_URL)
        cursor = conn.cursor()
        
        # Get scan images from database
        cursor.execute("""
            SELECT si.id, si.filename, si.original_filename, si.file_path, s.id as scan_id
            FROM scan_images si
            JOIN scans s ON si.scan_id = s.id
            ORDER BY si.id DESC
            LIMIT 10;
        """)
        
        scan_images = cursor.fetchall()
        
        if scan_images:
            print(f"📊 Found {len(scan_images)} recent scan images in database:")
            for img in scan_images:
                img_id, filename, original_filename, file_path, scan_id = img
                print(f"   ID: {img_id}, Scan: {scan_id}")
                print(f"   Filename: {filename}")
                print(f"   Original: {original_filename}")
                print(f"   Path: {file_path}")
                print()
        else:
            print("❌ No scan images found in database")
            
        cursor.close()
        conn.close()
        
        return scan_images
        
    except Exception as e:
        print(f"❌ Error checking database scan images: {e}")
        return []

def check_file_accessibility(scan_images):
    """Check if scan image files are accessible"""
    print("🔍 FILE ACCESSIBILITY CHECK")
    print("=" * 40)
    
    if not scan_images:
        print("❌ No scan images to check")
        return
        
    # Determine uploads path
    if os.path.exists("/app"):
        uploads_path = "/app/uploads"
    else:
        uploads_path = "uploads"
    
    accessible_count = 0
    
    for img in scan_images:
        img_id, filename, original_filename, file_path, scan_id = img
        
        # Try different possible file locations
        possible_paths = [
            os.path.join(uploads_path, filename) if filename else None,
            file_path if file_path else None,
            os.path.join(uploads_path, original_filename) if original_filename else None,
        ]
        
        found = False
        for path in possible_paths:
            if path and os.path.exists(path):
                try:
                    file_size = os.path.getsize(path)
                    print(f"✅ {filename} found at {path} ({file_size} bytes)")
                    accessible_count += 1
                    found = True
                    break
                except Exception as e:
                    print(f"❌ {filename} exists but error reading: {e}")
                    
        if not found:
            print(f"❌ {filename} NOT FOUND in any location")
            print(f"   Checked: {[p for p in possible_paths if p]}")
    
    print(f"\n📊 Summary: {accessible_count}/{len(scan_images)} scan images accessible")

def check_railway_volume_mount():
    """Check Railway volume mount information"""
    print("\n🗂️  RAILWAY VOLUME MOUNT CHECK")
    print("=" * 40)
    
    # Check Railway environment variables
    volume_name = os.getenv("RAILWAY_VOLUME_NAME")
    volume_mount_path = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
    
    if volume_name:
        print(f"✅ Volume name: {volume_name}")
    else:
        print("❌ RAILWAY_VOLUME_NAME not set")
        
    if volume_mount_path:
        print(f"✅ Volume mount path: {volume_mount_path}")
    else:
        print("❌ RAILWAY_VOLUME_MOUNT_PATH not set")
        
    # Check if volume is mounted
    if volume_mount_path and os.path.exists(volume_mount_path):
        print(f"✅ Volume mount path exists: {volume_mount_path}")
        try:
            files = os.listdir(volume_mount_path)
            print(f"📊 Found {len(files)} items in volume")
        except Exception as e:
            print(f"❌ Error listing volume: {e}")
    else:
        print(f"❌ Volume mount path does not exist or not set")

def test_file_upload_path():
    """Test where files would be uploaded"""
    print("\n📤 FILE UPLOAD PATH TEST")
    print("=" * 40)
    
    # Simulate the get_uploads_path() function logic
    if os.path.exists("/app") and os.getenv("RAILWAY_STATIC_URL"):
        uploads_path = "/app/uploads"
        print(f"✅ Railway platform detected, using: {uploads_path}")
    else:
        uploads_path = "uploads"
        print(f"❌ Not on Railway platform, using: {uploads_path}")
    
    # Check if path is writable
    try:
        test_file = os.path.join(uploads_path, "test_write.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print(f"✅ Upload path is writable: {uploads_path}")
    except Exception as e:
        print(f"❌ Upload path is not writable: {e}")

def main():
    """Main function to run all checks"""
    print("🚀 RAILWAY VOLUME & SCAN IMAGE CHECK")
    print("=" * 50)
    
    # Check Railway volume
    check_railway_volume()
    
    # Check database scan images
    scan_images = check_database_scan_images()
    
    # Check file accessibility
    check_file_accessibility(scan_images)
    
    # Check Railway volume mount
    check_railway_volume_mount()
    
    # Test file upload path
    test_file_upload_path()
    
    print("\n🔧 RECOMMENDATIONS:")
    print("1. If no images found in /app/uploads, they're not persisted in Railway volume")
    print("2. If volume mount variables are missing, add a volume to your Railway service")
    print("3. If files exist but aren't accessible, check file permissions")
    print("4. Consider re-uploading scan images to populate the volume")

if __name__ == "__main__":
    main() 