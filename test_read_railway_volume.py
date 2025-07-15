#!/usr/bin/env python3
"""
Test script to read files from a Railway volume
Usage: python test_read_railway_volume.py [railway_url] [filename]
Example: python test_read_railway_volume.py https://mtg-scan-development.up.railway.app volume_test_20250714_123456.txt
"""

import sys
import requests

def read_test_file(railway_url, filename=None):
    """Read file(s) from the Railway volume"""
    print(f"🔍 Testing read from Railway volume at: {railway_url}")
    
    try:
        # First, list all files in the volume
        list_response = requests.get(f"{railway_url}/api/list-uploads")
        if list_response.status_code != 200:
            print(f"❌ Failed to list files. Status code: {list_response.status_code}")
            print(f"Response: {list_response.text}")
            return False
            
        files = list_response.json().get('files', [])
        print(f"📋 Found {len(files)} files in volume")
        
        if filename:
            # If specific file requested, only show that one
            if filename not in files:
                print(f"❌ File not found: {filename}")
                return False
            files_to_read = [filename]
        else:
            # Otherwise show all test files
            files_to_read = [f for f in files if f.startswith('volume_test_')]
            
        # Read each file
        for test_file in files_to_read:
            print(f"\n📄 Reading file: {test_file}")
            response = requests.get(f"{railway_url}/uploads/{test_file}")
            
            if response.status_code == 200:
                content = response.text
                print(f"✅ Successfully read file")
                print(f"📝 Content: {content}")
            else:
                print(f"❌ Failed to read file. Status code: {response.status_code}")
                print(f"Response: {response.text}")
                
        return True
            
    except Exception as e:
        print(f"❌ Error reading from volume: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python test_read_railway_volume.py [railway_url] [optional_filename]")
        print("Example: python test_read_railway_volume.py https://mtg-scan-development.up.railway.app volume_test_20250714_123456.txt")
        sys.exit(1)
        
    railway_url = sys.argv[1].rstrip('/')
    filename = sys.argv[2] if len(sys.argv) == 3 else None
    read_test_file(railway_url, filename) 