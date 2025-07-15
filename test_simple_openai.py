#!/usr/bin/env python3
"""
Simple OpenAI API test - no images, just basic text completion
"""

import os
import requests
import time
from datetime import datetime

def test_simple_openai():
    """Test basic OpenAI API connectivity with simple text completion"""
    
    print(f"🔍 Testing simple OpenAI API at {datetime.now()}")
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found")
        return False
    
    print(f"🔑 API Key: {api_key[:10]}...")
    
    try:
        start_time = time.time()
        
        # Simple text completion - no images
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
                        'content': 'What is 2+2? Answer in one word.'
                    }
                ],
                'max_tokens': 10,
                'temperature': 0.0
            },
            timeout=30
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"⏱️  Response time: {elapsed_time:.2f} seconds")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            answer = data['choices'][0]['message']['content']
            print(f"✅ SUCCESS: OpenAI responded with: '{answer}'")
            return True
        else:
            print(f"❌ FAILED: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.ConnectTimeout:
        print("❌ CONNECTION TIMEOUT: Could not connect to OpenAI API")
        return False
    except requests.exceptions.ReadTimeout:
        print("❌ READ TIMEOUT: OpenAI API did not respond in time")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ CONNECTION ERROR: {e}")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_simple_openai()
    if success:
        print("\n🎉 OpenAI API connectivity test PASSED")
    else:
        print("\n🚨 OpenAI API connectivity test FAILED") 