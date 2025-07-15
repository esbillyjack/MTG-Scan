#!/usr/bin/env python3
"""
Sync scan images from development Railway volume to production Railway volume
"""

import requests

# Configuration
DEV_URL = "https://mtg-scan-development.up.railway.app"
PROD_URL = "https://mtg-scan-production.up.railway.app"


def get_images_from_development():
    """Get list of images from development volume using /api/list-uploads endpoint"""
    try:
        response = requests.get(f"{DEV_URL}/api/list-uploads")
        if response.status_code == 200:
            data = response.json()
            # Only sync image files (jpg, jpeg, png, webp)
            return [f for f in data.get('files', []) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        else:
            print(f"❌ Failed to get images from development: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error getting images from development: {e}")
        return []

def download_image_from_dev(image_name):
    """Download a single image from development"""
    try:
        response = requests.get(f"{DEV_URL}/uploads/{image_name}")
        if response.status_code == 200:
            return response.content
        else:
            print(f"❌ Failed to download {image_name}: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error downloading {image_name}: {e}")
        return None

def upload_image_to_production(image_name, image_data):
    """Upload a single image to production"""
    try:
        files = {'file': (image_name, image_data, 'image/jpeg')}
        response = requests.post(f"{PROD_URL}/upload", files=files)
        
        if response.status_code == 200:
            print(f"✅ Uploaded: {image_name}")
            return True
        else:
            print(f"❌ Failed to upload {image_name}: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error uploading {image_name}: {e}")
        return False

def main():
    print("🖼️  Syncing scan images from development to production...")
    print(f"📁 Source: {DEV_URL}/uploads/")
    print(f"🌐 Target: {PROD_URL}/uploads/")
    print()
    
    # Get list of images from development
    print("📋 Getting image list from development volume...")
    dev_images = get_images_from_development()
    
    if not dev_images:
        print("❌ No images found in development volume")
        return
    
    print(f"📊 Found {len(dev_images)} images in development volume")
    print()
    
    # Copy each image
    successful = 0
    failed = 0
    
    for image_name in sorted(dev_images):
        print(f"📥 Downloading: {image_name}")
        image_data = download_image_from_dev(image_name)
        
        if image_data:
            print(f"📤 Uploading: {image_name}")
            if upload_image_to_production(image_name, image_data):
                successful += 1
            else:
                failed += 1
        else:
            failed += 1
    
    print()
    print("📈 Sync Summary:")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {len(dev_images)}")
    
    if failed == 0:
        print("🎉 All images synced successfully!")
    else:
        print(f"⚠️  {failed} images failed to sync")

if __name__ == "__main__":
    main() 