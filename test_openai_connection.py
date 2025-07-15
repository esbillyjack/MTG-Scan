#!/usr/bin/env python3
"""
Test script to diagnose OpenAI API connectivity issues from Railway
"""

import os
import requests
import time
from datetime import datetime

def test_openai_connection():
    """Test basic connectivity to OpenAI API"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found")
        return False
    
    print(f"🔍 Testing OpenAI API connectivity at {datetime.now()}")
    print(f"🔑 API Key: {api_key[:10]}...")
    
    # Test basic API endpoint
    try:
        print("\n📡 Testing basic API endpoint...")
        response = requests.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10
        )
        print(f"✅ Status: {response.status_code}")
        if response.status_code == 200:
            models = response.json()
            print(f"✅ Found {len(models.get('data', []))} models")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    # Test simple completion
    try:
        print("\n🤖 Testing simple completion...")
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": "Say 'test'"}],
                "max_tokens": 5
            },
            timeout=30
        )
        print(f"✅ Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Response: {result['choices'][0]['message']['content']}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Completion failed: {e}")
        return False
    
    return True

def test_network_info():
    """Test network connectivity and DNS resolution"""
    print(f"\n🌐 Network diagnostics at {datetime.now()}")
    
    # Test DNS resolution
    try:
        import socket
        ip = socket.gethostbyname("api.openai.com")
        print(f"✅ DNS Resolution: api.openai.com -> {ip}")
    except Exception as e:
        print(f"❌ DNS Resolution failed: {e}")
    
    # Test external IP
    try:
        response = requests.get("https://ifconfig.me/ip", timeout=5)
        print(f"✅ External IP: {response.text.strip()}")
    except Exception as e:
        print(f"❌ External IP check failed: {e}")
    
    # Test basic internet connectivity
    try:
        response = requests.get("https://www.google.com", timeout=5)
        print(f"✅ Internet connectivity: {response.status_code}")
    except Exception as e:
        print(f"❌ Internet connectivity failed: {e}")

if __name__ == "__main__":
    print("🚀 OpenAI Connection Diagnostic Tool")
    print("=" * 50)
    
    test_network_info()
    test_openai_connection()
    
    print("\n" + "=" * 50)
    print("✅ Diagnostic complete") 