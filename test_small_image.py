#!/usr/bin/env python3
"""
Test script to create and process a very small image to test Railway payload theory
"""

import os
import base64
from PIL import Image, ImageDraw, ImageFont
import io

def create_tiny_test_image():
    """Create a very small test image with card-like content"""
    # Create a tiny 100x140 image (much smaller than real card scans)
    width, height = 100, 140
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Draw a simple card-like rectangle
    draw.rectangle([10, 10, 90, 130], outline='black', width=2)
    
    # Add some text to make it look like a card
    try:
        # Try to use a simple font
        font = ImageFont.load_default()
        draw.text((15, 20), "Lightning", fill='black', font=font)
        draw.text((15, 40), "Bolt", fill='black', font=font)
        draw.text((15, 70), "Deal 3", fill='black', font=font)
        draw.text((15, 90), "damage", fill='black', font=font)
    except:
        # If font fails, just use basic text
        draw.text((15, 20), "Lightning", fill='black')
        draw.text((15, 40), "Bolt", fill='black')
    
    # Save to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=85)
    img_byte_arr.seek(0)
    
    return img_byte_arr.getvalue()

def test_tiny_image_processing():
    """Test processing a tiny image through the AI pipeline"""
    print("🔍 Creating tiny test image...")
    
    # Create tiny image
    image_data = create_tiny_test_image()
    
    # Save to file
    test_image_path = "uploads/tiny_test_image.jpg"
    os.makedirs("uploads", exist_ok=True)
    
    with open(test_image_path, "wb") as f:
        f.write(image_data)
    
    # Get file info
    file_size = os.path.getsize(test_image_path)
    print(f"📊 Tiny image created: {file_size} bytes ({file_size/1024:.2f} KB)")
    
    # Convert to base64 to see payload size
    base64_data = base64.b64encode(image_data).decode('utf-8')
    print(f"📊 Base64 size: {len(base64_data)} characters")
    
    # Compare to large image
    large_image_base64_size = 384588  # From Railway logs
    print(f"📊 Size comparison: Tiny={len(base64_data)} vs Large={large_image_base64_size}")
    print(f"📊 Reduction factor: {large_image_base64_size / len(base64_data):.1f}x smaller")
    
    # Test with AI processor
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
        from ai_processor import CardRecognitionAI
        
        print("\n🤖 Testing with AI processor...")
        ai_processor = CardRecognitionAI()
        
        # Process the tiny image
        result = ai_processor.process_image(test_image_path)
        
        print(f"✅ AI Processing SUCCESS!")
        print(f"📊 Cards found: {len(result)}")
        
        if result:
            for i, card in enumerate(result):
                print(f"  Card {i+1}: {card.get('name', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI Processing FAILED: {e}")
        return False

if __name__ == "__main__":
    success = test_tiny_image_processing()
    if success:
        print("\n🎉 Tiny image test PASSED - Ready for Railway test!")
    else:
        print("\n🚨 Tiny image test FAILED") 