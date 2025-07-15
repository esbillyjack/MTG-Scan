#!/usr/bin/env python3
"""
Test script to verify Claude Vision API is working
"""

import os
import sys
import base64
from pathlib import Path

# Add the backend directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from backend.vision_processor_factory import ClaudeVisionProcessor
except ImportError as e:
    print(f"❌ Error importing ClaudeVisionProcessor: {e}")
    sys.exit(1)

def test_claude_vision():
    """Test Claude Vision API with a sample image"""
    
    print("🧪 Testing Claude Vision API...")
    
    # Check if API key is set
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found in environment variables")
        print("Please set your Anthropic API key in the .env file")
        return False
    
    print(f"✅ Found Anthropic API key: {api_key[:10]}...")
    
    # Use a known good image for testing
    test_image_path = Path("uploads/scan_175_4c61cf9d-7837-4538-847f-1888f70c0684.jpg")
    if not test_image_path.exists():
        print(f"❌ Known good test image not found: {test_image_path}")
        return False
    print(f"📷 Using test image: {test_image_path}")
    
    try:
        # Create Claude processor with config
        config = {
            'enabled': True,
            'timeout': 120,
            'max_retries': 3
        }
        processor = ClaudeVisionProcessor(config)
        
        print(f"📊 Image path: {test_image_path}")
        
        # Test the processor
        print("🔍 Processing image with Claude Vision...")
        result = processor.process_image(str(test_image_path))
        
        if result and len(result) > 0:
            print("✅ Claude Vision test successful!")
            for i, card in enumerate(result):
                print(f"📝 Card {i+1}: {card.get('name', 'Unknown')}")
                print(f"🎯 Set: {card.get('set', 'Unknown')}")
                print(f"🎯 Confidence: {card.get('confidence', 'N/A')}")
                if card.get('notes'):
                    print(f"📋 Notes: {card.get('notes')}")
            return True
        else:
            print("❌ Claude Vision test failed - no cards identified")
            return False
            
    except Exception as e:
        print(f"❌ Error during Claude Vision test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_claude_vision()
    if success:
        print("\n🎉 Claude Vision is working correctly!")
    else:
        print("\n💥 Claude Vision test failed. Check your API key and network connection.")
        sys.exit(1) 