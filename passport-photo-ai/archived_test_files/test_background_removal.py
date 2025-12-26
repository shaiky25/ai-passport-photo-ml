#!/usr/bin/env python3

import requests
import base64
from PIL import Image
import io

def test_background_removal():
    """Test background removal functionality specifically"""
    
    # Create a test image with a person on a colored background
    test_img = Image.new('RGB', (600, 600), (255, 0, 0))  # Red background
    
    # Add a simple "person" shape in the center
    from PIL import ImageDraw
    draw = ImageDraw.Draw(test_img)
    
    # Draw a simple person silhouette
    # Head (circle)
    draw.ellipse([250, 150, 350, 250], fill=(139, 69, 19))  # Brown for skin
    # Body (rectangle)
    draw.rectangle([275, 250, 325, 400], fill=(0, 0, 139))  # Dark blue for shirt
    # Arms
    draw.rectangle([225, 275, 275, 325], fill=(139, 69, 19))  # Left arm
    draw.rectangle([325, 275, 375, 325], fill=(139, 69, 19))  # Right arm
    
    # Save test image
    test_img.save('test_person_red_bg.jpg', 'JPEG')
    print("Created test person image with red background: test_person_red_bg.jpg")
    
    # Test background removal via API
    try:
        url = 'http://passport-photo-fixed.eba-mvpmm2ar.us-east-1.elasticbeanstalk.com/api/full-workflow'
        
        with open('test_person_red_bg.jpg', 'rb') as f:
            files = {'image': f}
            data = {
                'remove_background': 'true',  # Enable background removal
                'use_ai': 'true'
            }
            
            print("Testing background removal via API...")
            response = requests.post(url, files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('processed_image'):
                    # Decode and save the result
                    img_data = base64.b64decode(result['processed_image'])
                    with open('test_bg_removed.jpg', 'wb') as f:
                        f.write(img_data)
                    
                    print("✅ Background removal test successful: test_bg_removed.jpg")
                    print(f"Face detection: {result.get('analysis', {}).get('face_detection', {}).get('valid', 'Unknown')}")
                    
                    # Check if background was actually removed by looking at corners
                    result_img = Image.open(io.BytesIO(img_data))
                    corner_pixel = result_img.getpixel((10, 10))  # Top-left corner
                    print(f"Corner pixel color: {corner_pixel}")
                    
                    if corner_pixel == (255, 255, 255):
                        print("✅ Background appears to be white (removed successfully)")
                    elif corner_pixel == (255, 0, 0):
                        print("❌ Background is still red (removal failed)")
                    else:
                        print(f"⚠️ Background is different color: {corner_pixel}")
                    
                    return True
                else:
                    print(f"❌ API returned success=False: {result}")
                    return False
            else:
                print(f"❌ API request failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

    # Test without background removal for comparison
    try:
        print("\nTesting WITHOUT background removal for comparison...")
        with open('test_person_red_bg.jpg', 'rb') as f:
            files = {'image': f}
            data = {
                'remove_background': 'false',  # Disable background removal
                'use_ai': 'true'
            }
            
            response = requests.post(url, files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('processed_image'):
                    # Decode and save the result
                    img_data = base64.b64decode(result['processed_image'])
                    with open('test_bg_kept.jpg', 'wb') as f:
                        f.write(img_data)
                    
                    print("✅ No background removal test successful: test_bg_kept.jpg")
                    
                    # Check corner pixel
                    result_img = Image.open(io.BytesIO(img_data))
                    corner_pixel = result_img.getpixel((10, 10))
                    print(f"Corner pixel color (no removal): {corner_pixel}")
                    
    except Exception as e:
        print(f"❌ No removal test failed: {e}")

if __name__ == "__main__":
    test_background_removal()