#!/usr/bin/env python3
"""
Debug script to trace the entire image processing pipeline
"""

import os
import sys
import base64
import time
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from ai_processor import AIProcessor
    from database import Database
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

def debug_image_processing(image_path):
    """Debug the complete image processing pipeline with detailed logging"""
    
    print(f"\n🔍 DEBUG: Starting image processing pipeline at {datetime.now()}")
    print(f"📁 Image path: {image_path}")
    
    # Check if file exists
    if not os.path.exists(image_path):
        print(f"❌ ERROR: Image file does not exist: {image_path}")
        return False
    
    # Get file info
    file_size = os.path.getsize(image_path)
    print(f"📊 File size: {file_size} bytes ({file_size/1024/1024:.2f} MB)")
    
    # Step 1: Read file
    print(f"\n🔄 STEP 1: Reading file...")
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        print(f"✅ File read successfully: {len(image_data)} bytes")
    except Exception as e:
        print(f"❌ ERROR reading file: {e}")
        return False
    
    # Step 2: Base64 encode
    print(f"\n🔄 STEP 2: Base64 encoding...")
    try:
        start_time = time.time()
        base64_image = base64.b64encode(image_data).decode('utf-8')
        encode_time = time.time() - start_time
        print(f"✅ Base64 encoded: {len(base64_image)} characters in {encode_time:.2f}s")
    except Exception as e:
        print(f"❌ ERROR encoding: {e}")
        return False
    
    # Step 3: Initialize AI processor
    print(f"\n🔄 STEP 3: Initializing AI processor...")
    try:
        ai_processor = AIProcessor()
        print(f"✅ AI processor initialized")
        print(f"🔑 API key configured: {ai_processor.client.api_key[:10]}...")
    except Exception as e:
        print(f"❌ ERROR initializing AI processor: {e}")
        return False
    
    # Step 4: Process image
    print(f"\n🔄 STEP 4: Processing image with AI...")
    try:
        start_time = time.time()
        
        # Add detailed logging to the AI call
        print(f"📡 Making OpenAI API call...")
        print(f"📊 Model: gpt-4o")
        print(f"📊 Payload size: {len(base64_image)} characters")
        print(f"📊 Image format: data:image/jpeg;base64,...")
        
        result = ai_processor.process_image(base64_image)
        
        process_time = time.time() - start_time
        print(f"✅ AI processing completed in {process_time:.2f}s")
        print(f"📊 Result type: {type(result)}")
        
        if isinstance(result, dict):
            print(f"📊 Result keys: {list(result.keys()) if result else 'None'}")
            if 'cards' in result:
                print(f"📊 Cards found: {len(result['cards'])}")
        
        return result
        
    except Exception as e:
        print(f"❌ ERROR in AI processing: {e}")
        print(f"🔍 Exception type: {type(e)}")
        
        # Try to get more details about the error
        if hasattr(e, 'response'):
            print(f"🔍 Response status: {e.response.status_code if hasattr(e.response, 'status_code') else 'N/A'}")
            print(f"🔍 Response text: {e.response.text if hasattr(e.response, 'text') else 'N/A'}")
        
        return False

def main():
    """Main debug function"""
    
    print("🚀 Starting debug processing pipeline")
    
    # Environment info
    print(f"\n📍 Environment: {os.getenv('ENV_MODE', 'unknown')}")
    print(f"📍 Python version: {sys.version}")
    print(f"📍 Current directory: {os.getcwd()}")
    print(f"📍 OpenAI API key: {os.getenv('OPENAI_API_KEY', 'NOT SET')[:10]}...")
    
    # Find a test image
    image_path = None
    test_images = [
        'uploads/scan_138_99e414eb-e1da-41a5-bc10-1c2bb4079762.jpg',
        'uploads/scan_247_17942592-8cb9-421f-ba8b-092dbe76d4d6.jpg',
    ]
    
    for path in test_images:
        if os.path.exists(path):
            image_path = path
            break
    
    if not image_path:
        # Look for any scan image
        import glob
        images = glob.glob('uploads/scan_*.jpg')
        if images:
            image_path = images[0]
    
    if not image_path:
        print("❌ No test images found")
        return
    
    # Debug the processing
    result = debug_image_processing(image_path)
    
    if result:
        print(f"\n🎉 DEBUG SUCCESSFUL")
        print(f"📊 Final result: {result}")
    else:
        print(f"\n🚨 DEBUG FAILED")

if __name__ == "__main__":
    main() 