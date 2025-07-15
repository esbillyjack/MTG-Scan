#!/usr/bin/env python3
"""
Test script to specifically test OpenAI Vision API with image payload
"""

import os
import requests
import base64
import time
from datetime import datetime

def create_test_image_base64():
    """Create a test image base64 string similar to what the card scanner uses"""
    # Create a simple test image (1x1 pixel PNG)
    test_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
    return base64.b64encode(test_image_data).decode('utf-8')

def test_vision_api_small():
    """Test vision API with small image"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found")
        return False
    
    print(f"🔍 Testing OpenAI Vision API (small image) at {datetime.now()}")
    
    # Create small test image
    small_image = create_test_image_base64()
    print(f"📊 Small image size: {len(small_image)} base64 characters")
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What do you see in this image?"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{small_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 100,
                "temperature": 0.0
            },
            timeout=30
        )
        
        print(f"✅ Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ Response: {content[:100]}...")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Vision API (small) failed: {e}")
        return False

def test_vision_api_large():
    """Test vision API with large image (simulating card scanner payload)"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found")
        return False
    
    print(f"🔍 Testing OpenAI Vision API (large image) at {datetime.now()}")
    
    # Create large test image by repeating small image data
    small_image = create_test_image_base64()
    # Simulate the size of the card scanner images (~384k characters)
    large_image = small_image * 4000  # Approximate size
    print(f"📊 Large image size: {len(large_image)} base64 characters")
    
    try:
        start_time = time.time()
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What do you see in this image?"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{large_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 100,
                "temperature": 0.0
            },
            timeout=60
        )
        
        elapsed_time = time.time() - start_time
        print(f"⏱️  Request took: {elapsed_time:.2f} seconds")
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ Response: {content[:100]}...")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"⏱️  Request failed after: {elapsed_time:.2f} seconds")
        print(f"❌ Vision API (large) failed: {e}")
        return False

def test_actual_card_image():
    """Test with an actual card image file if available"""
    print(f"🔍 Testing with actual card image at {datetime.now()}")
    
    # Look for an actual uploaded image file
    import glob
    image_files = glob.glob("/app/uploads/scan_*.jpg")
    if not image_files:
        print("❌ No actual card images found in /app/uploads/")
        return False
    
    # Use the first image file
    image_path = image_files[0]
    print(f"📁 Using image: {image_path}")
    
    try:
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        print(f"📊 Actual image size: {len(image_data)} base64 characters")
        
        api_key = os.getenv("OPENAI_API_KEY")
        start_time = time.time()
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What do you see in this image?"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 100,
                "temperature": 0.0
            },
            timeout=60
        )
        
        elapsed_time = time.time() - start_time
        print(f"⏱️  Request took: {elapsed_time:.2f} seconds")
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ Response: {content[:100]}...")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"⏱️  Request failed after: {elapsed_time:.2f} seconds")
        print(f"❌ Actual card image test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 OpenAI Vision API Diagnostic Tool")
    print("=" * 50)
    
    # Test small image
    small_success = test_vision_api_small()
    print()
    
    # Test large image  
    large_success = test_vision_api_large()
    print()
    
    # Test actual card image
    actual_success = test_actual_card_image()
    print()
    
    print("=" * 50)
    print("📊 Results Summary:")
    print(f"Small image: {'✅ PASS' if small_success else '❌ FAIL'}")
    print(f"Large image: {'✅ PASS' if large_success else '❌ FAIL'}")
    print(f"Actual card image: {'✅ PASS' if actual_success else '❌ FAIL'}")
    print("=" * 50) 