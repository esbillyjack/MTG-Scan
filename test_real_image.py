#!/usr/bin/env python3
"""
Test OpenAI Vision API with a real card image from Railway
"""

import base64
import requests
import os
import time

def test_vision_with_real_image():
    """Test vision API with a real card image"""
    
    # Check if we have a real card image in uploads
    image_path = None
    if os.path.exists('uploads/scan_138_99e414eb-e1da-41a5-bc10-1c2bb4079762.jpg'):
        image_path = 'uploads/scan_138_99e414eb-e1da-41a5-bc10-1c2bb4079762.jpg'
    else:
        # Look for any scan image
        import glob
        images = glob.glob('uploads/scan_*.jpg')
        if images:
            image_path = images[0]
    
    if not image_path:
        print("❌ No card images found")
        return False
    
    print(f"📁 Testing with: {image_path}")
    
    # Get file info
    file_size = os.path.getsize(image_path)
    print(f"📊 File size: {file_size} bytes")
    
    # Encode image
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    print(f"📊 Base64 size: {len(image_data)} characters")
    
    # Test vision API
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ No OpenAI API key found")
        return False
    
    print(f"🔑 API Key: {api_key[:10]}...")
    
    try:
        start_time = time.time()
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-4o',
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {'type': 'text', 'text': 'What do you see in this image?'},
                            {
                                'type': 'image_url',
                                'image_url': {
                                    'url': f'data:image/jpeg;base64,{image_data}'
                                }
                            }
                        ]
                    }
                ],
                'max_tokens': 100,
                'temperature': 0.0
            },
            timeout=120  # 2 minute timeout
        )
        
        elapsed_time = time.time() - start_time
        print(f"⏱️  Request took: {elapsed_time:.2f} seconds")
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ Response: {content[:200]}...")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"⏱️  Request failed after: {elapsed_time:.2f} seconds")
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing OpenAI Vision API with Real Card Image")
    print("=" * 60)
    
    success = test_vision_with_real_image()
    
    print("=" * 60)
    if success:
        print("✅ Vision API test PASSED")
    else:
        print("❌ Vision API test FAILED") 