#!/usr/bin/env python3
"""
Sync all local scan images to Railway volume (via /upload endpoint)
"""

import os
import requests
import glob

def upload_image_to_railway(image_path, railway_url):
    """Upload a single image to Railway /upload endpoint"""
    try:
        filename = os.path.basename(image_path)
        with open(image_path, 'rb') as f:
            files = {'file': (filename, f, 'image/jpeg')}
            response = requests.post(f"{railway_url}/upload", files=files, timeout=30)
        if response.status_code == 200:
            print(f"✅ Uploaded: {filename}")
            return True
        else:
            print(f"❌ Failed to upload {filename}: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error uploading {os.path.basename(image_path)}: {e}")
        return False

def sync_all_images():
    """Sync all local scan images to Railway"""
    print("🔄 Starting image sync to Railway...")
    railway_url = "https://mtg-scan-development.up.railway.app"
    print(f"🌐 Railway URL: {railway_url}")
    image_patterns = ['uploads_backup/*.jpg', 'uploads_backup/*.jpeg', 'uploads_backup/*.png', 'uploads_backup/*.webp']
    all_images = []
    for pattern in image_patterns:
        all_images.extend(glob.glob(pattern))
    print(f"📁 Found {len(all_images)} images to upload")
    if not all_images:
        print("⚠️ No images found to upload")
        return
    success_count = 0
    for image_path in all_images:
        if upload_image_to_railway(image_path, railway_url):
            success_count += 1
    print(f"\n🎉 Sync completed!")
    print(f"✅ Successfully uploaded: {success_count}/{len(all_images)} images")
    if success_count < len(all_images):
        print(f"❌ Failed to upload: {len(all_images) - success_count} images")

if __name__ == "__main__":
    sync_all_images() 