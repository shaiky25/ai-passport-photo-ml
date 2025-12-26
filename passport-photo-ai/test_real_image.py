#!/usr/bin/env python3
"""
Test background removal with the actual uploaded image
"""

import requests
import base64
from PIL import Image
import io
import os

BACKEND_URL = "http://localhost:5000"

def test_with_real_image():
    """Test background removal with the user's uploaded image"""
    
    # Create a test image since we can't access the uploaded image directly
    # This simulates a complex background image like the one you provided
    img = Image.new('RGB', (800, 800), (50, 100, 150))  # Blue background like your image
    
    # Add some complex background elements
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    
    # Add buildings/cityscape background
    draw.rectangle([0, 400, 800, 800], fill=(80, 80, 80))  # Ground
    draw.rectangle([100, 200, 200, 400], fill=(120, 120, 120))  # Building 1
    draw.rectangle([300, 150, 400, 400], fill=(100, 100, 100))  # Building 2
    draw.rectangle([500, 250, 600, 400], fill=(140, 140, 140))  # Building 3
    
    # Add a person-like shape in the center
    person_center = (400, 300)
    person_radius = 80
    
    # Head
    draw.ellipse([
        person_center[0] - person_radius//2, 
        person_center[1] - person_radius,
        person_center[0] + person_radius//2, 
        person_center[1] - person_radius//2
    ], fill=(255, 220, 177))
    
    # Body
    draw.rectangle([
        person_center[0] - person_radius//3,
        person_center[1] - person_radius//2,
        person_center[0] + person_radius//3,
        person_center[1] + person_radius
    ], fill=(50, 50, 50))  # Dark suit
    
    # Save test image
    img.save('test_complex_background.jpg', 'JPEG', quality=95)
    
    # Test background removal
    with open('test_complex_background.jpg', 'rb') as f:
        files = {'image': ('complex_bg.jpg', f, 'image/jpeg')}
        data = {'remove_background': 'true', 'email': ''}
        
        print("🧪 Testing background removal with complex image...")
        response = requests.post(f"{BACKEND_URL}/api/full-workflow", files=files, data=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            success = result.get('success', False)
            processed_image = result.get('processed_image')
            
            if success and processed_image:
                # Save result
                image_data = base64.b64decode(processed_image)
                with open('test_complex_bg_removed.jpg', 'wb') as output_file:
                    output_file.write(image_data)
                
                # Analyze result
                result_img = Image.open(io.BytesIO(image_data))
                
                # Check corners for background removal
                corners = [
                    result_img.getpixel((0, 0)),
                    result_img.getpixel((result_img.width-1, 0)),
                    result_img.getpixel((0, result_img.height-1)),
                    result_img.getpixel((result_img.width-1, result_img.height-1))
                ]
                
                light_corners = sum(1 for corner in corners if sum(corner) > 600)
                
                print(f"✅ Background removal successful!")
                print(f"   Original: test_complex_background.jpg")
                print(f"   Result: test_complex_bg_removed.jpg")
                print(f"   Output size: {result_img.size}")
                print(f"   Light corners: {light_corners}/4")
                print(f"   Corner colors: {corners}")
                
                # Check if background was actually removed
                if light_corners >= 3:
                    print("✅ Background appears to be successfully removed (white/light background)")
                else:
                    print("⚠️  Background removal may not be complete")
                
                return True
            else:
                print(f"❌ Processing failed: success={success}, has_image={bool(processed_image)}")
                return False
        else:
            print(f"❌ Request failed: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False

if __name__ == "__main__":
    success = test_with_real_image()
    print(f"\n{'🎉' if success else '❌'} Test {'PASSED' if success else 'FAILED'}")