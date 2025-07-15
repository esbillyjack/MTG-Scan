#!/usr/bin/env python3
"""
Check if angelic_volume is properly configured and scan images are accessible
"""

import os
import sys
import psycopg2
import requests
from pathlib import Path
import json

# Database connection
PROD_DATABASE_URL = "postgresql://postgres:BicHTleuATnAIkRFBcqTDXMwwyuIXEAA@turntable.proxy.rlwy.net:35800/railway"

def check_railway_volume_config():
    """Check Railway volume configuration"""
    print("🔍 RAILWAY VOLUME CONFIGURATION CHECK")
    print("=" * 45)
    
    # Check Railway volume environment variables
    volume_name = os.getenv("RAILWAY_VOLUME_NAME")
    volume_mount_path = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
    
    print(f"📦 Volume Name: {volume_name or 'Not set'}")
    print(f"📁 Volume Mount Path: {volume_mount_path or 'Not set'}")
    
    # Check if we're on Railway platform
    railway_static_url = os.getenv("RAILWAY_STATIC_URL")
    railway_environment = os.getenv("RAILWAY_ENVIRONMENT")
    
    print(f"🚀 Railway Static URL: {railway_static_url or 'Not set'}")
    print(f"🌍 Railway Environment: {railway_environment or 'Not set'}")
    
    # Expected paths for angelic_volume
    expected_paths = [
        "/app/uploads",        # Standard Railway uploads path
        "/data",              # Common volume mount path
        "/mnt/angelic_volume", # Volume-specific mount path
        volume_mount_path     # Whatever is set in env var
    ]
    
    print(f"\n📂 CHECKING POSSIBLE VOLUME PATHS:")
    accessible_paths = []
    
    for path in expected_paths:
        if path:
            if os.path.exists(path):
                try:
                    files = os.listdir(path)
                    size = sum(os.path.getsize(os.path.join(path, f)) for f in files if os.path.isfile(os.path.join(path, f)))
                    print(f"✅ {path} - {len(files)} files, {size:,} bytes")
                    accessible_paths.append(path)
                except PermissionError:
                    print(f"❌ {path} - Permission denied")
                except Exception as e:
                    print(f"❌ {path} - Error: {e}")
            else:
                print(f"❌ {path} - Does not exist")
    
    return accessible_paths, volume_mount_path

def check_scan_images_in_volume(volume_paths):
    """Check if scan images are accessible in the volume"""
    print(f"\n🖼️  SCAN IMAGES IN VOLUME CHECK")
    print("=" * 45)
    
    # Get scan images from database
    try:
        conn = psycopg2.connect(PROD_DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT si.filename, si.file_path, s.id as scan_id
            FROM scan_images si
            JOIN scans s ON si.scan_id = s.id
            ORDER BY si.id DESC
            LIMIT 5;
        """)
        
        recent_images = cursor.fetchall()
        cursor.close()
        conn.close()
        
        print(f"📊 Checking {len(recent_images)} recent scan images from database:")
        
        found_count = 0
        
        for filename, file_path, scan_id in recent_images:
            print(f"\n🔍 Checking: {filename}")
            
            found = False
            for volume_path in volume_paths:
                possible_file_path = os.path.join(volume_path, filename)
                if os.path.exists(possible_file_path):
                    try:
                        file_size = os.path.getsize(possible_file_path)
                        print(f"   ✅ Found in {volume_path} ({file_size:,} bytes)")
                        found = True
                        found_count += 1
                        break
                    except Exception as e:
                        print(f"   ❌ Error reading from {volume_path}: {e}")
            
            if not found:
                print(f"   ❌ NOT FOUND in any volume path")
        
        print(f"\n📊 Summary: {found_count}/{len(recent_images)} recent scan images found in volume")
        
        return found_count > 0
        
    except Exception as e:
        print(f"❌ Error checking scan images: {e}")
        return False

def test_volume_write_access(volume_paths):
    """Test if we can write to the volume"""
    print(f"\n✏️  VOLUME WRITE ACCESS TEST")
    print("=" * 45)
    
    for volume_path in volume_paths:
        test_file = os.path.join(volume_path, "test_write.txt")
        try:
            with open(test_file, 'w') as f:
                f.write("Test write to volume")
            
            # Read it back
            with open(test_file, 'r') as f:
                content = f.read()
            
            # Clean up
            os.remove(test_file)
            
            print(f"✅ {volume_path} - Write access OK")
            return True
            
        except Exception as e:
            print(f"❌ {volume_path} - Write access failed: {e}")
    
    return False

def check_app_uploads_path_logic():
    """Check the get_uploads_path() function logic"""
    print(f"\n🔧 APP UPLOADS PATH LOGIC CHECK")
    print("=" * 45)
    
    # Simulate the logic from backend/app.py
    if os.path.exists("/app") and os.getenv("RAILWAY_STATIC_URL"):
        uploads_path = "/app/uploads"
        print(f"✅ Railway platform detected")
        print(f"📁 App will use: {uploads_path}")
    else:
        uploads_path = "uploads"
        print(f"❌ Not on Railway platform")
        print(f"📁 App will use: {uploads_path}")
    
    # Check if this path exists and is accessible
    if os.path.exists(uploads_path):
        try:
            files = os.listdir(uploads_path)
            print(f"✅ Path exists with {len(files)} files")
        except Exception as e:
            print(f"❌ Path exists but not accessible: {e}")
    else:
        print(f"❌ Path does not exist")
        
        # Try to create it
        try:
            os.makedirs(uploads_path, exist_ok=True)
            print(f"✅ Created directory: {uploads_path}")
        except Exception as e:
            print(f"❌ Cannot create directory: {e}")
    
    return uploads_path

def check_railway_api_endpoints():
    """Check Railway API endpoints"""
    print(f"\n🌐 RAILWAY API ENDPOINTS CHECK")
    print("=" * 45)
    
    # Try to determine Railway URL
    railway_url = os.getenv("RAILWAY_PUBLIC_DOMAIN")
    if railway_url and not railway_url.startswith("http"):
        railway_url = f"https://{railway_url}"
    
    if not railway_url:
        print("❌ Cannot determine Railway URL")
        return
    
    print(f"🔗 Testing Railway URL: {railway_url}")
    
    # Test endpoints
    endpoints = [
        "/api/environment",
        "/api/database/status", 
        "/scan/history"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{railway_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {endpoint} - OK")
            else:
                print(f"❌ {endpoint} - Status {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")

def main():
    """Main function to run all checks"""
    print("🚀 ANGELIC VOLUME CONFIGURATION CHECK")
    print("=" * 50)
    
    # Check volume configuration
    volume_paths, mount_path = check_railway_volume_config()
    
    if not volume_paths:
        print("\n❌ No accessible volume paths found!")
        print("🔧 RECOMMENDATIONS:")
        print("1. Verify angelic_volume is properly mounted")
        print("2. Check RAILWAY_VOLUME_MOUNT_PATH environment variable")
        print("3. Ensure volume mount path is /app/uploads or similar")
        return
    
    # Check scan images in volume
    images_found = check_scan_images_in_volume(volume_paths)
    
    # Test write access
    write_access = test_volume_write_access(volume_paths)
    
    # Check app uploads path logic
    app_uploads_path = check_app_uploads_path_logic()
    
    # Check Railway API endpoints
    check_railway_api_endpoints()
    
    # Summary
    print(f"\n📊 ANGELIC VOLUME SUMMARY")
    print("=" * 50)
    print(f"✅ Volume paths found: {len(volume_paths)}")
    print(f"{'✅' if images_found else '❌'} Scan images accessible: {images_found}")
    print(f"{'✅' if write_access else '❌'} Write access: {write_access}")
    print(f"📁 App uploads path: {app_uploads_path}")
    print(f"🔗 Mount path: {mount_path or 'Not configured'}")
    
    if volume_paths and not images_found:
        print(f"\n🔧 NEXT STEPS:")
        print("1. Volume is configured but scan images are missing")
        print("2. Upload scan images to the volume")
        print("3. Use Railway CLI or web interface to upload files")
        print("4. Files should go to:", volume_paths[0])
    elif not volume_paths:
        print(f"\n🔧 NEXT STEPS:")
        print("1. Configure angelic_volume mount path as /app/uploads")
        print("2. Redeploy the Railway service")
        print("3. Upload scan images to the volume")

if __name__ == "__main__":
    main() 