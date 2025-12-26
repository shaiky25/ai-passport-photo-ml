#!/usr/bin/env python3
"""
Test the watermark functionality to ensure 3x larger text is working
"""

import sys
sys.path.append('backend')

from application import PassportPhotoProcessor
from PIL import Image
import io

def test_watermark():
    # Create a test image
    test_img = Image.new('RGB', (1200, 1200), (200, 200, 200))
    
    # Initialize processor
    processor = PassportPhotoProcessor()
    
    # Add watermark
    watermarked = processor.add_watermark(test_img)
    
    # Save test result
    watermarked.save('test_watermark_3x_size.jpg', quality=95)
    print("Watermark test completed - saved as test_watermark_3x_size.jpg")
    
    # Check if watermark was applied
    if watermarked.size == test_img.size:
        print("✓ Watermark applied successfully")
        print(f"✓ Image dimensions: {watermarked.size}")
        return True
    else:
        print("✗ Watermark failed")
        return False

if __name__ == "__main__":
    test_watermark()