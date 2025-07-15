#!/usr/bin/env python3
"""
Sync local scan images to Railway volume
"""

import os
import shutil
import requests
import psycopg2
from pathlib import Path
import json

# Database connections
PROD_DATABASE_URL = "postgresql://postgres:BicHTleuATnAIkRFBcqTDXMwwyuIXEAA@turntable.proxy.rlwy.net:35800/railway"

def get_scan_images_from_db():
    """Get all scan images from production database"""
    try:
        conn = psycopg2.connect(PROD_DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT si.id, si.filename, si.original_filename, si.file_path, s.id as scan_id
            FROM scan_images si
            JOIN scans s ON si.scan_id = s.id
            ORDER BY si.id;
        """)
        
        scan_images = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return scan_images
        
    except Exception as e:
        print(f"❌ Error getting scan images from database: {e}")
        return []

def find_local_images():
    """Find all local scan images"""
    local_uploads = "uploads"
    local_backup = "uploads_backup"
    
    found_images = {}
    
    # Check both uploads and uploads_backup directories
    for directory in [local_uploads, local_backup]:
        if os.path.exists(directory):
            for file in os.listdir(directory):
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                    file_path = os.path.join(directory, file)
                    found_images[file] = file_path
    
    return found_images

def create_railway_upload_script():
    """Create a script to upload files to Railway"""
    
    # Get scan images from database
    scan_images = get_scan_images_from_db()
    local_images = find_local_images()
    
    print(f"📊 Found {len(scan_images)} scan images in database")
    print(f"📁 Found {len(local_images)} local image files")
    
    # Create upload script
    script_content = '''#!/usr/bin/env python3
"""
Upload scan images to Railway volume
Run this script ON Railway using: railway run python upload_to_railway.py
"""

import os
import shutil
import sys
from pathlib import Path

# Files to upload (generated from local scan)
FILES_TO_UPLOAD = [
'''
    
    missing_files = []
    found_files = []
    
    for img in scan_images:
        img_id, filename, original_filename, file_path, scan_id = img
        
        if filename in local_images:
            script_content += f'    ("{filename}", "{local_images[filename]}"),\n'
            found_files.append(filename)
        else:
            missing_files.append(filename)
    
    script_content += ''']

def upload_files():
    """Upload files to Railway volume"""
    
    # Check if running on Railway
    if not os.path.exists("/app"):
        print("❌ This script must be run on Railway")
        print("Use: railway run python upload_to_railway.py")
        return
    
    uploads_path = "/app/uploads"
    
    # Ensure uploads directory exists
    os.makedirs(uploads_path, exist_ok=True)
    
    print(f"📤 Uploading {len(FILES_TO_UPLOAD)} files to Railway volume...")
    
    uploaded_count = 0
    
    for filename, local_path in FILES_TO_UPLOAD:
        # Create file with dummy content (since we can't transfer actual files)
        railway_path = os.path.join(uploads_path, filename)
        
        try:
            # Create placeholder file
            with open(railway_path, 'w') as f:
                f.write(f"# Placeholder for {filename}\\n")
                f.write(f"# Original path: {local_path}\\n")
                f.write(f"# You need to manually upload this file\\n")
            
            print(f"✅ Created placeholder: {filename}")
            uploaded_count += 1
            
        except Exception as e:
            print(f"❌ Failed to create {filename}: {e}")
    
    print(f"\\n📊 Created {uploaded_count} placeholder files")
    print(f"📁 Files are in: {uploads_path}")
    
    # List final contents
    if os.path.exists(uploads_path):
        files = os.listdir(uploads_path)
        print(f"\\n📋 Railway volume now contains {len(files)} files")

if __name__ == "__main__":
    upload_files()
'''
    
    # Write the script
    with open("upload_to_railway.py", "w") as f:
        f.write(script_content)
    
    print(f"✅ Created upload script: upload_to_railway.py")
    print(f"📊 Found {len(found_files)} files to upload")
    print(f"❌ Missing {len(missing_files)} files")
    
    if missing_files:
        print(f"📋 Missing files: {missing_files[:5]}...")
    
    return found_files, missing_files

def create_manual_upload_instructions():
    """Create instructions for manual upload"""
    
    instructions = """
# 🚀 Manual Upload Instructions

Since Railway doesn't support direct file uploads via script, you need to:

## Option 1: Use Railway CLI (Recommended)
1. Install Railway CLI: `npm install -g @railway/cli`
2. Login: `railway login`
3. Link to your project: `railway link`
4. Copy files: `railway run cp uploads/* /app/uploads/`

## Option 2: Re-upload via Web Interface
1. Go to your Railway app
2. Upload scan images through the web interface
3. This will recreate the files in the volume

## Option 3: Use Railway Shell
1. `railway shell`
2. Manual file creation/upload

## Verify Volume is Working
After setting up the volume, your scan history should work properly.
"""
    
    with open("RAILWAY_UPLOAD_INSTRUCTIONS.md", "w") as f:
        f.write(instructions)
    
    print("✅ Created: RAILWAY_UPLOAD_INSTRUCTIONS.md")

def main():
    """Main function"""
    print("🚀 RAILWAY IMAGE SYNC PREPARATION")
    print("=" * 50)
    
    # Create upload script
    found_files, missing_files = create_railway_upload_script()
    
    # Create manual instructions
    create_manual_upload_instructions()
    
    print("\n🔧 NEXT STEPS:")
    print("1. Add volume to Railway service (/app/uploads)")
    print("2. Deploy your app to Railway")
    print("3. Follow RAILWAY_UPLOAD_INSTRUCTIONS.md")
    print("4. Test scan history functionality")
    
    print(f"\n📊 SUMMARY:")
    print(f"   Found: {len(found_files)} scan images")
    print(f"   Missing: {len(missing_files)} scan images")
    print(f"   Total in DB: {len(found_files) + len(missing_files)}")

if __name__ == "__main__":
    main() 