#!/usr/bin/env python3
"""
Test script to check Railway volume contents and file access
"""

import requests
import os

def test_railway_volume():
    """Test what's available in the Railway volume"""
    
    railway_url = "https://mtg-scan-development.up.railway.app"
    
    print("🔍 Testing Railway volume access...")
    print(f"🌐 Railway URL: {railway_url}")
    
    # Test 1: Check if we can access the volume listing endpoint
    try:
        response = requests.get(f"{railway_url}/api/volume-test", timeout=10)
        print(f"📋 Volume test endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"📄 Response: {response.text}")
    except Exception as e:
        print(f"❌ Volume test endpoint failed: {e}")
    
    # Test 2: Try to access a specific image file
    test_files = [
        "scan_163_60505061-e377-4c7e-b0e9-f50a893b4919.jpg",
        "aggressive_test_1_1752380328.jpg",
        "test_1_1752379494.jpg"
    ]
    
    print("\n🖼️ Testing specific image access:")
    for filename in test_files:
        try:
            response = requests.get(f"{railway_url}/uploads/{filename}", timeout=10)
            print(f"📁 {filename}: {response.status_code} ({len(response.content)} bytes)")
            if response.status_code == 404:
                print(f"   ❌ File not found in Railway volume")
            elif response.status_code == 200:
                print(f"   ✅ File found and accessible")
        except Exception as e:
            print(f"❌ Error accessing {filename}: {e}")
    
    # Test 3: Check database status to see what the app thinks about storage
    try:
        response = requests.get(f"{railway_url}/api/database/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            storage_info = data.get('storage', {})
            print(f"\n📊 Storage info from Railway app:")
            print(f"   Type: {storage_info.get('type', 'Unknown')}")
            print(f"   Path: {storage_info.get('path', 'Unknown')}")
            print(f"   Total files: {storage_info.get('total_files', 'Unknown')}")
            print(f"   Total size: {storage_info.get('total_size', 'Unknown')}")
        else:
            print(f"❌ Database status failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting database status: {e}")

if __name__ == "__main__":
    test_railway_volume() 