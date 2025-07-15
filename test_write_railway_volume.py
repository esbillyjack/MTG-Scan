#!/usr/bin/env python3
"""
Test script to write a test image to a Railway volume
Usage: python test_write_railway_volume.py [railway_url]
Example: python test_write_railway_volume.py https://mtg-scan-development.up.railway.app
"""

import sys
import requests
from datetime import datetime
from PIL import Image
import io

def create_test_image():
    """Create a small test image with timestamp"""
    # Create a 100x100 red image with timestamp
    img = Image.new('RGB', (100, 100))
    # Fill with red color
    img.paste((255, 0, 0), [0, 0, 100, 100])
    
    # Convert to bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()
    
    return img_byte_arr

def write_test_file(railway_url):
    """Write a test image to the Railway volume"""
    print(f"🎯 Testing write to Railway volume at: {railway_url}")
    
    # Create test image with timestamp in filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_filename = f"volume_test_{timestamp}.jpg"
    test_content = create_test_image()
    
    try:
        # Upload the test image
        files = {'file': (test_filename, test_content, 'image/jpeg')}
        response = requests.post(f"{railway_url}/upload", files=files)
        
        if response.status_code == 200:
            print(f"✅ Successfully wrote test image: {test_filename}")
            return test_filename
        else:
            print(f"❌ Failed to write file. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error writing to volume: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_write_railway_volume.py [railway_url]")
        print("Example: python test_write_railway_volume.py https://mtg-scan-development.up.railway.app")
        sys.exit(1)
        
    railway_url = sys.argv[1].rstrip('/')
    write_test_file(railway_url) 