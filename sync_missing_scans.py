#!/usr/bin/env python3
"""
Sync missing scan files from development to production Railway volumes
"""

import requests
import time

DEV_URL = "https://mtg-scan-development.up.railway.app"
PROD_URL = "https://mtg-scan-production.up.railway.app"

def get_scan_files(url):
    """Get list of scan files from specified environment"""
    try:
        response = requests.get(f"{url}/api/list-uploads")
        if response.status_code != 200:
            print(f"❌ Failed to list files from {url}")
            return []
            
        files = response.json().get('files', [])
        return [f for f in files if f.startswith('scan_')]
    except Exception as e:
        print(f"❌ Error getting files from {url}: {e}")
        return []

def download_from_dev(filename):
    """Download a file from development"""
    try:
        response = requests.get(f"{DEV_URL}/uploads/{filename}")
        if response.status_code == 200:
            return response.content
        else:
            print(f"❌ Failed to download {filename}: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error downloading {filename}: {e}")
        return None

def upload_to_prod(filename, file_data):
    """Upload a file to production"""
    try:
        files = {'file': (filename, file_data, 'image/jpeg')}
        response = requests.post(f"{PROD_URL}/upload", files=files)
        
        if response.status_code == 200:
            print(f"✅ Uploaded: {filename}")
            return True
        else:
            print(f"❌ Failed to upload {filename}: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error uploading {filename}: {e}")
        return False

def sync_missing_files():
    """Sync files that exist in development but not in production"""
    print("🔄 Syncing missing scan files from development to production...")
    
    # Get file lists
    print("\n📋 Getting file lists...")
    dev_files = set(get_scan_files(DEV_URL))
    prod_files = set(get_scan_files(PROD_URL))
    
    if not dev_files:
        print("❌ Failed to get development files")
        return
    if not prod_files:
        print("❌ Failed to get production files")
        return
    
    # Find missing files
    missing_files = dev_files - prod_files
    missing_files = sorted(list(missing_files))
    
    print(f"\n📊 Found {len(missing_files)} files to sync:")
    for file in missing_files:
        print(f"  - {file}")
    
    # Confirm and sync
    print(f"\n🚀 Starting sync of {len(missing_files)} files...")
    
    successful = 0
    failed = 0
    
    for i, filename in enumerate(missing_files, 1):
        print(f"\n[{i}/{len(missing_files)}] Processing: {filename}")
        
        # Download from development
        print("📥 Downloading from development...")
        file_data = download_from_dev(filename)
        
        if file_data:
            # Upload to production
            print("📤 Uploading to production...")
            if upload_to_prod(filename, file_data):
                successful += 1
            else:
                failed += 1
        else:
            failed += 1
        
        # Small delay to avoid overwhelming the servers
        time.sleep(0.5)
    
    # Print summary
    print("\n📈 Sync Summary:")
    print(f"✅ Successfully synced: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total files processed: {len(missing_files)}")
    
    if failed == 0:
        print("\n🎉 All files synced successfully!")
    else:
        print(f"\n⚠️  {failed} files failed to sync")

if __name__ == "__main__":
    sync_missing_files() 