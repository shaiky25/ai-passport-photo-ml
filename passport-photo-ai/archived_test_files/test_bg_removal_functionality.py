#!/usr/bin/env python3
"""
Test the background removal functionality with rembg
"""

import sys
sys.path.append('backend')

from application import PassportPhotoProcessor
from PIL import Image
import io

def test_bg_removal():
    # Create a test image with some content
    test_img = Image.new('RGB', (800, 800), (100, 150, 200))
    
    # Add a simple "person" shape in the center
    from PIL import ImageDraw
    draw = ImageDraw.Draw(test_img)
    draw.ellipse([300, 200, 500, 600], fill=(220, 180, 140))  # Face color
    
    # Save test input
    test_img.save('test_bg_input.jpg', quality=95)
    
    # Initialize processor
    processor = PassportPhotoProcessor()
    
    # Test background removal
    try:
        result_img = processor.remove_background_lightweight(test_img)
        result_img.save('test_bg_removed.jpg', quality=95)
        print("✓ Background removal test completed")
        print(f"✓ Input size: {test_img.size}")
        print(f"✓ Output size: {result_img.size}")
        return True
    except Exception as e:
        print(f"✗ Background removal failed: {e}")
        return False

if __name__ == "__main__":
    test_bg_removal()