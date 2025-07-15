#!/usr/bin/env python3
"""
Test script to verify both OpenAI and Claude vision processors are available
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_vision_processors():
    """Test both vision processors"""
    print("🔍 Testing Vision Processor Factory...")
    
    try:
        from backend.vision_processor_factory import get_vision_processor_factory
        factory = get_vision_processor_factory()
        
        print(f"✅ Factory loaded successfully")
        print(f"🎯 Current processor: {factory.get_current_processor_name()}")
        
        # Check processor status
        status = factory.get_processor_status()
        print(f"\n📊 Processor Status:")
        for name, info in status.items():
            enabled = "✅" if info['enabled'] else "❌"
            available = "✅" if info['available'] else "❌"
            print(f"  {name}: Enabled={enabled} Available={available}")
        
        # Test with tiny image
        print(f"\n🔍 Testing with tiny image...")
        test_image = "uploads/tiny_test_image.jpg"
        
        if os.path.exists(test_image):
            result = factory.process_image(test_image)
            print(f"✅ Processing successful!")
            print(f"📊 Cards found: {len(result)}")
            for i, card in enumerate(result):
                print(f"  Card {i+1}: {card.get('name', 'Unknown')}")
        else:
            print(f"⚠️ Test image not found: {test_image}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vision_processors() 