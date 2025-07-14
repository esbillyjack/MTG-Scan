#!/usr/bin/env python3
"""
Test Railway fallback system for serving scan images
"""

import os
import requests
from backend.app import RAILWAY_URL, USE_RAILWAY_FILES, UPLOADS_DIR

def test_railway_fallback():
    """Test if Railway fallback is working"""
    print("🔧 Testing Railway fallback system...")
    
    # Test file that exists on Railway but not locally
    test_filename = "scan_155_0732d342-cd02-40ca-88cf-f1af75b4144f.jpg"
    
    print(f"📁 Local uploads directory: {UPLOADS_DIR}")
    print(f"🌐 Railway URL: {RAILWAY_URL}")
    print(f"🔗 Railway fallback enabled: {USE_RAILWAY_FILES}")
    
    # Check if file exists locally
    local_path = os.path.join(UPLOADS_DIR, test_filename)
    local_exists = os.path.exists(local_path)
    print(f"📄 Local file exists: {local_exists}")
    
    # Check if file exists on Railway
    if RAILWAY_URL:
        railway_url = f"{RAILWAY_URL}/uploads/{test_filename}"
        try:
            response = requests.get(railway_url, timeout=10)
            railway_exists = response.status_code == 200
            print(f"🌐 Railway file exists: {railway_exists} (status: {response.status_code})")
        except Exception as e:
            print(f"❌ Railway check failed: {e}")
            railway_exists = False
    else:
        print("❌ Railway URL not configured")
        railway_exists = False
    
    # Test the fallback logic
    if not local_exists and railway_exists and USE_RAILWAY_FILES:
        print("✅ Backup system should work - file available on Railway")
        return True
    elif local_exists:
        print("✅ File available locally")
        return True
    else:
        print("❌ Backup system broken - file not available anywhere")
        return False

if __name__ == "__main__":
    # Set environment variables for testing
    os.environ['RAILWAY_APP_URL'] = 'https://mtg-scan-development.up.railway.app'
    os.environ['USE_RAILWAY_FILES'] = 'true'
    
    success = test_railway_fallback()
    if success:
        print("\n🎯 Railway fallback system is working!")
    else:
        print("\n❌ Railway fallback system needs fixing!") 