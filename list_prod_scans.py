#!/usr/bin/env python3
"""
List all scan filenames from the production Railway environment
"""

import sys
import requests

PROD_URL = "https://mtg-scan-production.up.railway.app"

def list_scan_files():
    """List all scan files from production volume"""
    print(f"🔍 Listing scan files from: {PROD_URL}")
    
    try:
        # Get list of all files
        response = requests.get(f"{PROD_URL}/api/list-uploads")
        if response.status_code != 200:
            print(f"❌ Failed to list files. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return
            
        files = response.json().get('files', [])
        
        # Filter for scan files (they start with 'scan_')
        scan_files = [f for f in files if f.startswith('scan_')]
        scan_files.sort()
        
        print(f"\n📊 Found {len(scan_files)} scan files:")
        for file in scan_files:
            # Extract scan ID from filename (format: scan_ID_UUID.ext)
            scan_id = file.split('_')[1] if len(file.split('_')) > 1 else 'unknown'
            print(f"Scan {scan_id}: {file}")
            
    except Exception as e:
        print(f"❌ Error listing files: {e}")

if __name__ == "__main__":
    list_scan_files() 